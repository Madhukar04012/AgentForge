"""Provider base class and message types."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


@dataclass
class ChatResponse:
    content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


class LLMProvider(abc.ABC):
    """Abstract LLM provider. Implementations wrap a specific vendor SDK."""

    name: str = "base"

    @abc.abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        raise NotImplementedError