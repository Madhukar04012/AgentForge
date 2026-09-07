"""Agent base classes."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from agentforge.providers.base import LLMProvider, Message
from agentforge.tools.registry import ToolRegistry


@dataclass
class AgentResult:
    """The output of an agent run."""

    final_answer: str
    messages: list[Message] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0


class Agent(abc.ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        provider: LLMProvider,
        tools: ToolRegistry,
        system_prompt: str | None = None,
        max_iterations: int = 8,
    ) -> None:
        if max_iterations <= 0:
            raise ValueError("max_iterations must be positive")
        self.provider = provider
        self.tools = tools
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.max_iterations = max_iterations

    @abc.abstractmethod
    def run(self, prompt: str) -> AgentResult:
        """Run the agent against a user prompt and return a final answer."""
        raise NotImplementedError