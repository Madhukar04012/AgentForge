"""A central registry for tools."""

from __future__ import annotations

from threading import RLock
from typing import Iterable

from agentforge.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._lock = RLock()

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("Tool.name must be non-empty")
        with self._lock:
            if tool.name in self._tools:
                raise ValueError(f"Tool already registered: {tool.name}")
            self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        with self._lock:
            self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        with self._lock:
            return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        with self._lock:
            return name in self._tools

    def __len__(self) -> int:
        with self._lock:
            return len(self._tools)

    def all(self) -> list[Tool]:
        with self._lock:
            return list(self._tools.values())

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self.all()]

    def extend(self, tools: Iterable[Tool]) -> None:
        for tool in tools:
            self.register(tool)