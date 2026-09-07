# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Runtime bridge: load AgentVersion → invoke provider → persist events.

The bridge is **synchronous** and **DB-session-driven**. The Arq
worker hands us a SQLAlchemy session and the Execution id; we load
everything we need from the session, run the provider, and write
events back to the same session. Each :func:`run_execution` call is
a single transactional unit of work — we commit at the end and
return a :class:`RunOutcome` describing what happened.

The function is deliberately small and easy to test: it has no
hidden globals, no I/O outside the DB and the provider, and no
async/await.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Mapping, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..models.agent import Agent, AgentVersion
from ..models.execution import Execution, ExecutionEvent, ExecutionStatus
from ..providers import (
    ModelProvider,
    ProviderError,
    ProviderNotConfigured,
    ProviderRequest,
    ProviderStreamEvent,
    get_provider,
)
from ..schemas.agent import AgentVersionConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Outcome.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunOutcome:
    """The result of a :func:`run_execution` call.

    The worker inspects ``status`` to decide whether to retry, send
    a notification, etc. The bridge itself does not retry.
    """

    execution_id: str
    status: ExecutionStatus
    output: Optional[str] = None
    error: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    latency_ms: Optional[int] = None


# ---------------------------------------------------------------------------
# Event vocabulary.
# ---------------------------------------------------------------------------
#
# We persist provider events using a small, stable vocabulary. The
# event_type is a short snake_case string. The payload is a JSON
# object whose shape depends on the event_type. The frontend only
# needs to know these types:
#
#   execution.started  — emitted exactly once at the start
#   model.request      — pre-invocation (records what we sent)
#   model.text         — a text chunk from the model
#   tool.call          — model requested a tool
#   tool.result        — result returned to the model
#   model.response     — the final aggregated response metadata
#   execution.completed
#   execution.failed
#


_EVENT_EXECUTION_STARTED = "execution.started"
_EVENT_MODEL_REQUEST = "model.request"
_EVENT_MODEL_TEXT = "model.text"
_EVENT_TOOL_CALL = "tool.call"
_EVENT_TOOL_RESULT = "tool.result"
_EVENT_MODEL_RESPONSE = "model.response"
_EVENT_EXECUTION_COMPLETED = "execution.completed"
_EVENT_EXECUTION_FAILED = "execution.failed"


# ---------------------------------------------------------------------------
# Bridge.
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _append_event(
    db: Session,
    execution: Execution,
    sequence: int,
    event_type: str,
    payload: Optional[Mapping[str, Any]] = None,
) -> ExecutionEvent:
    """Insert one :class:`ExecutionEvent` row.

    We use the session the worker handed us. The bridge does **not**
    commit; the worker is responsible for the transaction boundary
    so the entire run is atomic.
    """
    sanitized = _scrub_payload(event_type, payload)
    event = ExecutionEvent(
        execution_id=execution.id,
        sequence=sequence,
        event_type=event_type,
        payload=sanitized,
        occurred_at=_now(),
    )
    db.add(event)
    db.flush()  # populate event.id without committing
    return event


def _scrub_payload(
    event_type: str, payload: Optional[Mapping[str, Any]]
) -> Optional[dict]:
    """Sanitize an event payload before persisting.

    We always store a dict (or ``None``). The shape depends on
    ``event_type``; consumers must handle missing keys gracefully.
    """
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        return {"_raw": str(payload)[:1024]}
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            continue
        if key.lower() in {"api_key", "authorization", "bearer"}:
            continue
        if isinstance(value, str):
            out[key] = value[:8192]
        elif isinstance(value, (int, float, bool)) or value is None:
            out[key] = value
        elif isinstance(value, Mapping):
            out[key] = {str(k): v for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            out[key] = [str(v)[:1024] for v in value]
        else:
            out[key] = str(value)[:1024]
    return out


def _coerce_version_config(raw: Any) -> AgentVersionConfig:
    """Validate the JSON config against the Pydantic schema.

    We re-validate on every read, not just on write, so a corrupted
    or outdated row fails loudly at runtime rather than producing
    a half-configured invocation.
    """
    try:
        return AgentVersionConfig.model_validate(raw)
    except ValidationError as exc:
        raise ProviderError(
            f"AgentVersion.config failed validation: {exc}"
        ) from exc


def _provider_request(
    agent_version: AgentVersion, config: AgentVersionConfig, user_input: str
) -> ProviderRequest:
    return ProviderRequest(
        agent_version_id=agent_version.id,
        model_provider=config.model_provider,
        model_name=config.model_name,
        system_prompt=config.system_prompt,
        user_input=user_input,
        generation_config=config.generation_config.model_dump(exclude_none=True),
        tools=[t.model_dump() for t in config.tools],
    )


def _payload_for_event(ev: ProviderStreamEvent) -> dict:
    if ev.kind == "model_text":
        return {"text": ev.text}
    if ev.kind == "tool_call":
        return {"name": ev.name, "args": dict(ev.args or {})}
    if ev.kind == "tool_result":
        return {"name": ev.name, "output": ev.output}
    if ev.kind == "done":
        return {
            "output": ev.output,
            "usage": dict(ev.usage) if ev.usage else None,
        }
    return {"kind": ev.kind}


def _record_provider_event(
    db: Session,
    execution: Execution,
    sequence: int,
    ev: ProviderStreamEvent,
) -> int:
    """Persist a :class:`ProviderStreamEvent` and return next seq."""
    if ev.kind == "model_text":
        event_type = _EVENT_MODEL_TEXT
    elif ev.kind == "tool_call":
        event_type = _EVENT_TOOL_CALL
    elif ev.kind == "tool_result":
        event_type = _EVENT_TOOL_RESULT
    elif ev.kind == "done":
        event_type = _EVENT_MODEL_RESPONSE
    else:
        # Unknown kinds are persisted as generic "model.event" rows
        # so we never silently drop data.
        event_type = "model.event"
    _append_event(db, execution, sequence, event_type, _payload_for_event(ev))
    return sequence + 1


def _fail_execution(
    db: Session,
    execution: Execution,
    sequence: int,
    error: str,
) -> int:
    """Mark the execution failed and emit a closing event."""
    execution.status = ExecutionStatus.FAILED
    execution.error = error[:8000]
    execution.completed_at = _now()
    _append_event(db, execution, sequence, _EVENT_EXECUTION_FAILED, {"error": error})
    return sequence + 1


def _complete_execution(
    db: Session,
    execution: Execution,
    sequence: int,
    output: str,
    tokens_in: Optional[int],
    tokens_out: Optional[int],
    latency_ms: int,
) -> int:
    """Mark the execution completed and emit a closing event."""
    execution.status = ExecutionStatus.COMPLETED
    execution.output = output[:64_000]
    execution.completed_at = _now()
    if tokens_in is not None:
        execution.tokens_in = tokens_in
    if tokens_out is not None:
        execution.tokens_out = tokens_out
    execution.latency_ms = latency_ms
    _append_event(
        db,
        execution,
        sequence,
        _EVENT_EXECUTION_COMPLETED,
        {
            "output_preview": output[:512],
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
        },
    )
    return sequence + 1


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------


def run_execution(db: Session, execution_id: str) -> RunOutcome:
    """Execute a single :class:`Execution` synchronously.

    The caller (Arq worker, or a sync test) is responsible for
    committing or rolling back ``db``. The function flushes
    inserts so generated ids are populated, but does not commit.

    Returns a :class:`RunOutcome` describing the final state.
    """
    execution: Optional[Execution] = (
        db.query(Execution).filter(Execution.id == execution_id).one_or_none()
    )
    if execution is None:
        raise LookupError(f"Execution {execution_id!r} not found")

    sequence = 1  # 1-based, monotonic per execution
    started = time.monotonic()

    if execution.status not in (ExecutionStatus.QUEUED,):
        # Idempotency: if the execution is already running or
        # terminal, do nothing. The worker re-enqueues at most
        # once; any further attempts become a no-op.
        return RunOutcome(
            execution_id=execution.id,
            status=execution.status,
            output=execution.output,
            error=execution.error,
        )

    # Load the agent + version (eagerly, so we fail fast on
    # orphaned rows).
    agent: Optional[Agent] = (
        db.query(Agent).filter(Agent.id == execution.agent_id).one_or_none()
    )
    version: Optional[AgentVersion] = (
        db.query(AgentVersion)
        .filter(AgentVersion.id == execution.agent_version_id)
        .one_or_none()
    )
    if agent is None or version is None:
        msg = f"Execution {execution.id} references missing agent or version."
        sequence = _fail_execution(db, execution, sequence, msg)
        db.commit()
        return RunOutcome(
            execution_id=execution.id,
            status=ExecutionStatus.FAILED,
            error=msg,
        )

    if version.agent_id != agent.id:
        msg = (
            f"Execution {execution.id} agent_version_id "
            f"{version.id!r} does not belong to agent "
            f"{agent.id!r}."
        )
        sequence = _fail_execution(db, execution, sequence, msg)
        db.commit()
        return RunOutcome(
            execution_id=execution.id,
            status=ExecutionStatus.FAILED,
            error=msg,
        )

    # Transition to RUNNING.
    execution.status = ExecutionStatus.RUNNING
    execution.started_at = _now()
    _append_event(
        db,
        execution,
        sequence,
        _EVENT_EXECUTION_STARTED,
        {
            "agent_id": agent.id,
            "agent_version_id": version.id,
            "version_number": version.version_number,
        },
    )
    sequence += 1
    db.flush()

    # Resolve + validate provider.
    try:
        config = _coerce_version_config(version.config)
    except ProviderError as exc:
        sequence = _fail_execution(db, execution, sequence, str(exc))
        db.commit()
        return RunOutcome(
            execution_id=execution.id,
            status=ExecutionStatus.FAILED,
            error=str(exc),
        )

    try:
        provider: ModelProvider = get_provider(config.model_provider)
    except ProviderNotConfigured as exc:
        sequence = _fail_execution(db, execution, sequence, str(exc))
        db.commit()
        return RunOutcome(
            execution_id=execution.id,
            status=ExecutionStatus.FAILED,
            error=str(exc),
        )

    # Record what we're about to send (no secrets; no API keys).
    request = _provider_request(version, config, execution.input)
    _append_event(
        db,
        execution,
        sequence,
        _EVENT_MODEL_REQUEST,
        {
            "model_provider": request.model_provider,
            "model_name": request.model_name,
            "system_prompt_length": len(request.system_prompt),
            "input_length": len(request.user_input),
            "tools": [t.get("name") for t in request.tools],
        },
    )
    sequence += 1
    db.flush()

    # Drive the provider.
    events: List[ProviderStreamEvent] = []
    try:
        for ev in provider.invoke(request):
            events.append(ev)
            sequence = _record_provider_event(db, execution, sequence, ev)
            db.flush()
    except ProviderError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        execution.latency_ms = latency_ms
        sequence = _fail_execution(db, execution, sequence, str(exc))
        db.commit()
        return RunOutcome(
            execution_id=execution.id,
            status=ExecutionStatus.FAILED,
            error=str(exc),
            latency_ms=latency_ms,
        )
    except Exception as exc:  # noqa: BLE001 - we sanitize below
        latency_ms = int((time.monotonic() - started) * 1000)
        execution.latency_ms = latency_ms
        sanitized = _sanitize_unexpected(exc)
        sequence = _fail_execution(db, execution, sequence, sanitized)
        db.commit()
        return RunOutcome(
            execution_id=execution.id,
            status=ExecutionStatus.FAILED,
            error=sanitized,
            latency_ms=latency_ms,
        )

    # Aggregate final response.
    response = provider.final_response(events)
    latency_ms = int((time.monotonic() - started) * 1000)

    output = response.output or ""
    if not output:
        output = "(model produced no text output)"
        logger.warning(
            "Execution %s produced no text output (provider=%s, model=%s)",
            execution.id,
            request.model_provider,
            request.model_name,
        )

    sequence = _complete_execution(
        db,
        execution,
        sequence,
        output,
        response.tokens_in,
        response.tokens_out,
        latency_ms,
    )
    db.commit()

    return RunOutcome(
        execution_id=execution.id,
        status=ExecutionStatus.COMPLETED,
        output=output,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _sanitize_unexpected(exc: BaseException) -> str:
    """Best-effort safe text for an unexpected exception."""
    msg = str(exc) or repr(exc)
    msg = msg.replace("\n", " ").replace("\r", " ")
    for needle in ("key=", "Bearer ", "bearer "):
        idx = msg.lower().find(needle.lower())
        while idx != -1:
            msg = msg[:idx] + msg[idx + 60 + len(needle) :]
            idx = msg.lower().find(needle.lower())
    if len(msg) > 800:
        msg = msg[:800] + "…"
    return f"Unexpected error: {type(exc).__name__}: {msg}"
