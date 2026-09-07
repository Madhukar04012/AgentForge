"""Anthropic provider."""

from __future__ import annotations

import os
from typing import Any

from agentforge.providers.base import ChatResponse, LLMProvider, Message


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-5", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        # Stubbed — real implementation requires the anthropic SDK.
        raise NotImplementedError("AnthropicProvider.chat requires the anthropic package")