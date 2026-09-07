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

"""Executions router.

Implements:

  * ``POST /api/v1/executions`` — create a new :class:`Execution`
    in ``QUEUED`` state and enqueue it for the Arq worker. Returns
    the execution row immediately; the caller can poll
    ``GET /executions/{id}`` for status.
  * ``GET  /api/v1/executions`` — list executions in the caller's
    workspace, most recent first.
  * ``GET  /api/v1/executions/{id}`` — fetch one execution with
    its full event log.

We do **not** stream events over SSE in this milestone. The web UI
polls the event log. (SSE lands in a later phase.) The endpoint
returns the event log inline so the page can render immediately
on first load.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_or_create_default_workspace
from ..models.agent import Agent, AgentVersion
from ..models.execution import Execution, ExecutionStatus
from ..models.workspace import User, Workspace
from ..schemas.execution import (
    ExecutionCreateIn,
    ExecutionEventOut,
    ExecutionOut,
    ExecutionWithEventsOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/executions", tags=["executions"])


# ---------------------------------------------------------------------------
# Queue dispatch (soft import).
# ---------------------------------------------------------------------------


def _enqueue(execution_id: str) -> None:
    """Enqueue an execution for the Arq worker.

    We do a soft import of :mod:`agentforge_api.worker` so the API
    can boot in environments where Arq / Redis are not available
    (e.g. a freshly-cloned dev box running pytest). When the worker
    module is missing, we log a warning and return — the API stays
    usable, and ``POST /executions`` still creates the row in
    ``QUEUED`` state. The row will simply stay ``queued`` until a
    worker process is started.
    """
    try:
        from ..worker import enqueue_execution  # type: ignore
    except ImportError as exc:
        logger.warning(
            "agentforge_api.worker not importable; execution %s will "
            "stay in QUEUED until a worker process is started: %s",
            execution_id,
            exc,
        )
        return
    try:
        enqueue_execution(execution_id)
    except Exception as exc:  # noqa: BLE001 - we don't want queue errors to 500 the request
        logger.warning(
            "Failed to enqueue execution %s: %s", execution_id, exc
        )


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _load_agent_version(
    db: Session, workspace_id: str, agent_id: str, version_id: str
) -> tuple[Agent, AgentVersion]:
    agent = db.query(Agent).filter(Agent.id == agent_id).one_or_none()
    if agent is None or agent.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    version = (
        db.query(AgentVersion)
        .filter(
            AgentVersion.id == version_id,
            AgentVersion.agent_id == agent.id,
        )
        .one_or_none()
    )
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Agent version {version_id!r} not found for agent "
                f"{agent_id!r}"
            ),
        )
    return agent, version


# ---------------------------------------------------------------------------
# Routes.
# ---------------------------------------------------------------------------


@router.get("", response_model=List[ExecutionOut])
def list_executions(
    db: Annotated[Session, Depends(get_db)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> list[ExecutionOut]:
    rows = (
        db.query(Execution)
        .filter(Execution.workspace_id == workspace.id)
        .order_by(Execution.queued_at.desc())
        .limit(200)
        .all()
    )
    return [ExecutionOut.model_validate(r) for r in rows]


@router.post(
    "", response_model=ExecutionOut, status_code=status.HTTP_201_CREATED
)
def create_execution(
    payload: ExecutionCreateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> ExecutionOut:
    """Create a queued execution and dispatch it to the worker."""
    agent, version = _load_agent_version(
        db, workspace.id, payload.agent_id, payload.agent_version_id
    )

    now = datetime.now(tz=timezone.utc)
    execution = Execution(
        workspace_id=workspace.id,
        agent_id=agent.id,
        agent_version_id=version.id,
        status=ExecutionStatus.QUEUED,
        input=payload.input,
        queued_at=now,
        triggered_by_id=user.id,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    _enqueue(execution.id)
    return ExecutionOut.model_validate(execution)


@router.get("/{execution_id}", response_model=ExecutionWithEventsOut)
def get_execution(
    execution_id: str,
    db: Annotated[Session, Depends(get_db)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> ExecutionWithEventsOut:
    """Fetch a single execution and its full event log."""
    execution = (
        db.query(Execution)
        .filter(
            Execution.id == execution_id,
            Execution.workspace_id == workspace.id,
        )
        .one_or_none()
    )
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    # Eagerly load events (already ordered by sequence via the
    # relationship order_by). We touch the attribute to trigger the
    # load even when the relationship was not pre-populated.
    events = list(execution.events)
    return ExecutionWithEventsOut(
        id=execution.id,
        workspace_id=execution.workspace_id,
        agent_id=execution.agent_id,
        agent_version_id=execution.agent_version_id,
        status=execution.status.value
        if hasattr(execution.status, "value")
        else str(execution.status),
        input=execution.input,
        output=execution.output,
        error=execution.error,
        tokens_in=execution.tokens_in,
        tokens_out=execution.tokens_out,
        cost_usd=execution.cost_usd,
        latency_ms=execution.latency_ms,
        queued_at=execution.queued_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        triggered_by_id=execution.triggered_by_id,
        events=[ExecutionEventOut.model_validate(e) for e in events],
    )


__all__ = ["router"]
