"""A deterministic mock provider for tests."""

from __future__ import annotations

from typing import Any

from agentforge.providers.base import ChatResponse, LLMProvider, Message


class MockProvider(LLMProvider):
    """Returns scripted responses in order, then falls back to a default."""

    name = "mock"

    def __init__(self, scripted: list[ChatResponse] | None = None, default: str = "OK") -> None:
        self._scripted = list(scripted or [])
        self._default = default

    def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        if self._scripted:
            return self._scripted.pop(0)
        return ChatResponse(content=self._default)