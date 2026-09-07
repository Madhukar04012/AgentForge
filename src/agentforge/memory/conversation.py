"""Conversation memory — append-only message history with optional trimming."""

from __future__ import annotations

from collections import deque
from typing import Iterable

from agentforge.providers.base import Message


class ConversationMemory:
    """Bounded conversation history. Oldest messages are dropped first."""

    def __init__(self, max_messages: int = 100) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages must be positive")
        self._messages: deque[Message] = deque(maxlen=max_messages)

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def extend(self, messages: Iterable[Message]) -> None:
        for m in messages:
            self._messages.append(m)

    def clear(self) -> None:
        self._messages.clear()

    def messages(self) -> list[Message]:
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)