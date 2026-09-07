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

"""Google ADK-backed provider.

This is the **one** fully-implemented provider in Phase 2. It
delegates the actual model call to Google ADK's ``LlmAgent`` +
``Runner`` pair, translates the ADK ``Event`` stream into our
:class:`ProviderStreamEvent` vocabulary, and surfaces any
configuration error (e.g. missing ``GOOGLE_API_KEY`` /
``GEMINI_API_KEY``) as a :class:`ProviderNotConfigured` so the
worker can record a clear failure on the ``Execution`` row.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Iterator, Mapping, Optional

from .base import (
    ModelProvider,
    ProviderInvocationError,
    ProviderNotConfigured,
    ProviderRequest,
    ProviderResponse,
    ProviderStreamEvent,
    register_provider,
)

logger = logging.getLogger(__name__)


# Env vars the ADK Gemini integration looks at. ADK's
# ``google.adk.models.Gemini`` reads from ``GOOGLE_API_KEY`` first
# and falls back to ``GEMINI_API_KEY``. We mirror that here.
_GOOGLE_API_KEY_ENVS = ("GOOGLE_API_KEY", "GEMINI_API_KEY")


def _read_google_api_key() -> Optional[str]:
    """Return the first non-empty Google API key from the environment."""
    for name in _GOOGLE_API_KEY_ENVS:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    return None


@register_provider
class GoogleProvider(ModelProvider):
    """Google ADK provider (Gemini family).

    Uses ``google.adk.models.Gemini`` + ``google.adk.agents.LlmAgent``
    + ``google.adk.runners.Runner`` under the hood. ADK is imported
    lazily so the rest of the API can boot on a machine that does
    not have google-adk installed (e.g. lightweight CI runners).
    """

    name = "google"

    def __init__(self) -> None:
        self._api_key = _read_google_api_key()
        if not self._api_key:
            raise ProviderNotConfigured(
                "Google provider requires GOOGLE_API_KEY or "
                "GEMINI_API_KEY to be set in the environment."
            )

    @classmethod
    def is_configured(cls) -> bool:
        return _read_google_api_key() is not None

    # ------------------------------------------------------------------
    # invoke()
    # ------------------------------------------------------------------
    def invoke(
        self, request: ProviderRequest
    ) -> Iterator[ProviderStreamEvent]:
        """Run a single ADK invocation synchronously and yield events.

        Strategy:

          1. Build an :class:`LlmAgent` with the version's system
             prompt, model name, and generation config.
          2. Build a :class:`Runner` backed by an in-memory session
             service. Each call gets a fresh session id so
             concurrent invocations do not see each other's state.
          3. Call :meth:`Runner.run_debug` (synchronous, returns
             ``list[Event]``) — simpler than the async generator
             and suitable for the Arq worker pool.
          4. Walk the events and translate each one into a
             :class:`ProviderStreamEvent`. A final ``done`` event
             is emitted with aggregated usage metadata.
        """
        try:
            from google.adk.agents import LlmAgent
            from google.adk.models import Gemini
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types as genai_types
        except ImportError as exc:  # pragma: no cover - import guard
            raise ProviderNotConfigured(
                "google-adk is not installed. Run "
                "`pip install google-adk google-genai` to enable "
                "the Google provider."
            ) from exc

        agent = LlmAgent(
            name=f"agentforge-{request.agent_version_id[:8]}",
            model=Gemini(model=request.model_name),
            instruction=request.system_prompt or "",
            description="AgentForge runtime agent",
            tools=[],  # Phase 2: no tools yet. Future phases will translate
                       # request.tools into ADK FunctionTools.
        )

        session_service = InMemorySessionService()
        app_name = f"agentforge-{uuid.uuid4().hex[:8]}"
        user_id = f"agentforge-user-{uuid.uuid4().hex[:8]}"
        session_id = f"agentforge-session-{uuid.uuid4().hex[:12]}"

        runner = Runner(
            app_name=app_name,
            agent=agent,
            session_service=session_service,
            auto_create_session=True,
        )

        new_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=request.user_input)],
        )

        try:
            events = list(
                runner.run(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=new_message,
                )
            )
        except Exception as exc:  # noqa: BLE001 - we sanitize below
            raise ProviderInvocationError(
                f"Google ADK invocation failed: {_scrub(exc)}"
            ) from exc

        usage_metadata: Optional[Mapping[str, Any]] = None
        final_text_chunks: list[str] = []
        tool_call_seen = False

        for ev in events:
            if ev.error_code or ev.error_message:
                raise ProviderInvocationError(
                    f"ADK reported error "
                    f"(code={ev.error_code!r}): "
                    f"{_scrub(ev.error_message)}"
                )

            content = ev.content
            if content is None:
                continue
            parts = getattr(content, "parts", None) or []
            for part in parts:
                # Text part.
                text = getattr(part, "text", None)
                if text:
                    final_text_chunks.append(text)
                    yield ProviderStreamEvent(kind="model_text", text=text)
                # Function-call part.
                function_call = getattr(part, "function_call", None)
                if function_call is not None:
                    tool_call_seen = True
                    name = getattr(function_call, "name", "") or ""
                    args = _safe_args(getattr(function_call, "args", None))
                    yield ProviderStreamEvent(
                        kind="tool_call", name=name, args=args
                    )
                # Function-response part (result of a tool call).
                function_response = getattr(part, "function_response", None)
                if function_response is not None:
                    name = getattr(function_response, "name", "") or ""
                    response = getattr(function_response, "response", None)
                    output = _stringify_tool_output(response)
                    yield ProviderStreamEvent(
                        kind="tool_result", name=name, output=output
                    )

            if getattr(ev, "usage_metadata", None):
                usage_metadata = _usage_to_mapping(ev.usage_metadata)

        # If the model emitted only tool calls (no text yet) and we
        # have not produced a final assistant turn, that's still a
        # valid invocation — but the worker will want a non-empty
        # ``output`` field. The runtime bridge fills in a generic
        # placeholder so the Execution row is never NULL when the
        # status is COMPLETED.
        if not final_text_chunks and tool_call_seen:
            final_text_chunks.append("[model requested tool calls]")

        yield ProviderStreamEvent(
            kind="done",
            output="".join(final_text_chunks).strip(),
            usage=usage_metadata,
        )

    # ------------------------------------------------------------------
    # final_response()
    # ------------------------------------------------------------------
    def final_response(
        self, events: list[ProviderStreamEvent]
    ) -> ProviderResponse:
        out = super().final_response(events)
        # If the bridge lost the final "done" event's text (it
        # happens when the model produced only tool calls), make
        # sure the persisted Execution.output is non-empty.
        if not out.output:
            tool_outputs = [ev.output for ev in events if ev.kind == "tool_result"]
            if tool_outputs:
                out = ProviderResponse(
                    output="\n".join(tool_outputs).strip(),
                    tokens_in=out.tokens_in,
                    tokens_out=out.tokens_out,
                    cost_usd=out.cost_usd,
                    raw=out.raw,
                )
        return out


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _scrub(exc: BaseException) -> str:
    """Return a safe single-line representation of an exception.

    ADK / genai error messages occasionally echo back the request
    URL which may include an API key as ``?key=…``. We aggressively
    strip anything that looks like a key.
    """
    msg = str(exc) or repr(exc)
    msg = msg.replace("\n", " ").replace("\r", " ")
    # Drop common key leak patterns. Conservative — better to
    # over-strip than leak.
    for needle in ("key=", "Bearer ", "bearer "):
        idx = msg.lower().find(needle)
        while idx != -1:
            # Drop the needle + the next 60 chars.
            msg = msg[:idx] + msg[idx + 60 + len(needle) :]
            idx = msg.lower().find(needle)
    if len(msg) > 500:
        msg = msg[:500] + "…"
    return msg


def _safe_args(args: Any) -> Mapping[str, Any]:
    """Coerce an ADK function-call args object into a dict."""
    if args is None:
        return {}
    if isinstance(args, Mapping):
        return dict(args)
    if hasattr(args, "items"):
        try:
            return {k: v for k, v in args.items()}  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return {}
    # Last resort: try Pydantic model_dump if available.
    dump = getattr(args, "model_dump", None)
    if callable(dump):
        try:
            dumped = dump()
            if isinstance(dumped, Mapping):
                return dict(dumped)
        except Exception:  # noqa: BLE001
            return {}
    return {"_raw": str(args)}


def _stringify_tool_output(response: Any) -> str:
    """Best-effort stringification of a tool response payload."""
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if isinstance(response, (int, float, bool)):
        return str(response)
    if isinstance(response, Mapping):
        return ", ".join(f"{k}={v!r}" for k, v in response.items())
    dump = getattr(response, "model_dump", None)
    if callable(dump):
        try:
            dumped = dump()
            if isinstance(dumped, Mapping):
                return ", ".join(f"{k}={v!r}" for k, v in dumped.items())
        except Exception:  # noqa: BLE001
            pass
    return str(response)


def _usage_to_mapping(usage: Any) -> Mapping[str, Any]:
    """Translate an ADK ``Event.usage_metadata`` into a plain dict."""
    if usage is None:
        return {}
    # google.genai's UsageMetadata is a Pydantic model. Use
    # model_dump if available, otherwise fall back to attribute
    # access.
    dump = getattr(usage, "model_dump", None)
    if callable(dump):
        try:
            dumped = dump()
            if isinstance(dumped, Mapping):
                return dict(dumped)
        except Exception:  # noqa: BLE001
            pass
    return {
        "prompt_token_count": getattr(usage, "prompt_token_count", None),
        "candidates_token_count": getattr(usage, "candidates_token_count", None),
        "total_token_count": getattr(usage, "total_token_count", None),
    }
