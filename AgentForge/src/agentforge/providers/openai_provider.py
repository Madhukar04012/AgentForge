"""OpenAI provider."""

from __future__ import annotations

import os
from typing import Any

from agentforge.providers.base import ChatResponse, LLMProvider, Message


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        # Real implementation would call openai.OpenAI().chat.completions.create(...)
        # Kept as a thin stub so the package has zero runtime dependency on openai.
        raise NotImplementedError("OpenAIProvider.chat requires the openai package")