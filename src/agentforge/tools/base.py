"""Base Tool protocol and result types."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolContext:
    """Per-run context shared across tool invocations."""

    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result returned by a tool's run() method."""

    output: Any
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Tool(abc.ABC):
    """Base class for all tools."""

    name: str = ""
    description: str = ""

    @abc.abstractmethod
    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the tool and return a result."""
        raise NotImplementedError

    def schema(self) -> dict[str, Any]:
        """JSON-Schema-style description for the LLM."""
        return {
            "name": self.name,
            "description": self.description,
        }