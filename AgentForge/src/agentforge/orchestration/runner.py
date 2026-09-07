"""High-level runner — orchestrates an agent and surfaces run lifecycle hooks."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable

from agentforge.agents.base import Agent, AgentResult

log = logging.getLogger(__name__)


@dataclass
class RunHooks:
    """Optional callbacks invoked around a run. All fields default to no-ops."""

    on_start: Callable[[str], None] = field(default=lambda _prompt: None)
    on_end: Callable[[AgentResult], None] = field(default=lambda _result: None)
    on_error: Callable[[BaseException], None] = field(default=lambda _exc: None)


class Runner:
    """Runs an agent with optional timing and hooks."""

    def __init__(self, agent: Agent, hooks: RunHooks | None = None) -> None:
        self.agent = agent
        self.hooks = hooks or RunHooks()

    def run(self, prompt: str) -> AgentResult:
        self.hooks.on_start(prompt)
        start = time.monotonic()
        try:
            result = self.agent.run(prompt)
        except Exception as exc:
            log.exception("Agent run failed")
            self.hooks.on_error(exc)
            raise
        elapsed = time.monotonic() - start
        log.debug("Run finished in %.3fs, iterations=%d", elapsed, result.iterations)
        self.hooks.on_end(result)
        return result