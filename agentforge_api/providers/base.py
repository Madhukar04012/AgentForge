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

"""Provider ABC, registry, and request/response dataclasses.

The provider layer is intentionally small: a single synchronous
``invoke()`` method that takes a :class:`ProviderRequest` and yields
:class:`ProviderStreamEvent` objects. The runtime bridge is
responsible for translating those events into the persisted
``ExecutionEvent`` vocabulary.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Mapping, Optional


class ProviderError(RuntimeError):
    """Base class for provider-layer errors."""


class ProviderNotConfigured(ProviderError):
    """Raised when a provider id is not configured in this environment.

    Distinct from :class:`ProviderError` so the worker can convert
    it to a 4xx-ish "not configured" status rather than treating it
    as a generic 5xx internal failure.
    """


class ProviderInvocationError(ProviderError):
    """The provider is configured but the upstream call failed.

    The exception message must be safe to surface to the user. We
    do **not** echo back raw provider SDK errors that may contain
    API keys; the worker sanitizes before writing to the DB.
    """


@dataclass(frozen=True)
class ProviderRequest:
    """Inputs to a single model invocation.

    Attributes:
        agent_version_id: The immutable AgentVersion we are running
            against. Included for logging / telemetry.
        model_provider: The provider id (e.g. ``"google"``).
        model_name: The model id (e.g. ``"gemini-2.0-flash"``).
        system_prompt: The agent's instruction text.
        user_input: The end-user message.
        generation_config: Provider-agnostic knobs (temperature,
            top_p, max_output_tokens, …). Optional.
        tools: Provider-agnostic tool specs (``list[dict]``).
            Phase 2 ships an empty list; later phases will add
            function tools.
    """

    agent_version_id: str
    model_provider: str
    model_name: str
    system_prompt: str
    user_input: str
    generation_config: Mapping[str, Any] = field(default_factory=dict)
    tools: list[Mapping[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ProviderStreamEvent:
    """A single event yielded by :meth:`ModelProvider.invoke`.

    The runtime bridge translates these into ``ExecutionEvent``
    rows. We deliberately keep the schema tiny in Phase 2:

      * ``kind="model_text"`` — a chunk of model text output.
        ``text`` is the partial content.
      * ``kind="tool_call"`` — a tool call request from the model.
        ``name`` is the tool name; ``args`` is the parsed JSON
        arguments (dict).
      * ``kind="tool_result"`` — the result of a tool call.
        ``name`` and ``args`` mirror the request; ``output`` is
        the tool's return value (str).
      * ``kind="done"`` — the model has finished. ``output`` is the
        concatenated final assistant text.
    """

    kind: str
    text: str = ""
    name: str = ""
    args: Optional[Mapping[str, Any]] = None
    output: str = ""
    usage: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class ProviderResponse:
    """The final result of an invocation.

    The bridge persists this on the ``Execution`` row (output,
    tokens, latency, cost).
    """

    output: str
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    raw: Optional[Mapping[str, Any]] = None


class ModelProvider(abc.ABC):
    """Abstract base class for a model provider.

    Subclasses must implement :meth:`invoke` (the synchronous
    generator that yields :class:`ProviderStreamEvent` objects) and
    :meth:`is_configured` (a classmethod that returns ``True`` when
    the provider's required credentials are present in the
    environment).
    """

    #: Stable id used in ``AgentVersion.config["model_provider"]``.
    name: str = ""

    @abc.abstractmethod
    def invoke(
        self, request: ProviderRequest
    ) -> "Iterator[ProviderStreamEvent]":
        """Run a single invocation and yield stream events."""

    @classmethod
    @abc.abstractmethod
    def is_configured(cls) -> bool:
        """Return True iff this provider can run in the current environment.

        Implementations should check the environment for the
        credentials they need (e.g. ``GOOGLE_API_KEY`` for the
        Google provider). If a key is missing, return ``False``;
        the worker will then call :meth:`invoke` and the provider
        will raise :class:`ProviderNotConfigured` with a helpful
        message.
        """

    def final_response(
        self, events: "list[ProviderStreamEvent]"
    ) -> ProviderResponse:
        """Default reducer from stream events to a final response.

        Providers that need richer aggregation (e.g. Anthropic's
        tool-use blocks) override this.
        """
        chunks: list[str] = []
        usage: Optional[Mapping[str, Any]] = None
        for ev in events:
            if ev.kind == "model_text":
                chunks.append(ev.text)
            elif ev.kind == "done":
                if ev.usage is not None:
                    usage = ev.usage
        output = "".join(chunks).strip()
        tokens_in = None
        tokens_out = None
        if isinstance(usage, Mapping):
            ti = usage.get("tokens_in") or usage.get("input_tokens")
            to = usage.get("tokens_out") or usage.get("output_tokens")
            if isinstance(ti, int):
                tokens_in = ti
            if isinstance(to, int):
                tokens_out = to
        return ProviderResponse(
            output=output,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            raw={"usage": dict(usage) if usage else None},
        )


# ---------------------------------------------------------------------------
# Provider registry.
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, type["ModelProvider"]] = {}


def register_provider(cls: type["ModelProvider"]) -> type["ModelProvider"]:
    """Class decorator that registers a :class:`ModelProvider` subclass.

    Raises :class:`ValueError` if a provider with the same ``name``
    is already registered.
    """
    if not cls.name:
        raise ValueError(
            f"{cls.__name__}.name must be a non-empty string "
            "(used as the AgentVersion.config['model_provider'] value)"
        )
    if cls.name in _REGISTRY:
        raise ValueError(
            f"Provider {cls.name!r} is already registered "
            f"({_REGISTRY[cls.name].__name__})"
        )
    _REGISTRY[cls.name] = cls
    return cls


def get_provider(name: str) -> "ModelProvider":
    """Return a configured instance for the given provider id.

    Raises :class:`ProviderNotConfigured` if the id is unknown or
    the provider's ``is_configured()`` returns ``False``.
    """
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ProviderNotConfigured(
            f"Unknown model provider {name!r}. "
            f"Known providers: {sorted(_REGISTRY)}"
        )
    if not cls.is_configured():
        raise ProviderNotConfigured(
            f"Model provider {name!r} is not configured in this "
            f"environment. Set the required credentials and restart."
        )
    return cls()


def registered_provider_ids() -> list[str]:
    """Return the list of provider ids currently registered.

    Used by the API to surface the available providers to the UI.
    """
    return sorted(_REGISTRY)
