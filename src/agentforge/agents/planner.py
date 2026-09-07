"""Planner/Executor agent — generate a plan, then execute it step by step."""

from __future__ import annotations

import json
import logging
from typing import Any

from agentforge.agents.base import Agent, AgentResult
from agentforge.providers.base import Message
from agentforge.tools.base import ToolContext

log = logging.getLogger(__name__)


class PlannerAgent(Agent):
    """First ask the model for a plan, then execute each step with tool calls."""

    PLAN_SYSTEM = (
        "You are a planner. Given a user request, produce a JSON list of steps. "
        "Each step is an object with keys: 'thought' (str) and 'tool' (str|null) "
        "and 'args' (object). Return ONLY JSON — no prose, no markdown fences."
    )

    def run(self, prompt: str) -> AgentResult:
        plan_messages = [
            Message(role="system", content=self.PLAN_SYSTEM),
            Message(role="user", content=prompt),
        ]
        plan_response = self.provider.chat(plan_messages)
        plan = self._parse_plan(plan_response.content or "")

        messages: list[Message] = [Message(role="system", content=self.system_prompt)]
        tool_calls: list[dict[str, Any]] = []
        ctx = ToolContext()

        for step in plan[: self.max_iterations]:
            tool_name = step.get("tool")
            args = step.get("args") or {}
            if not tool_name:
                continue
            tool = self.tools.get(tool_name)
            if tool is None:
                tool_calls.append({"name": tool_name, "args": args, "observation": "Unknown tool"})
                continue
            try:
                result = tool.run(args, ctx)
                tool_calls.append({"name": tool_name, "args": args, "observation": result.output})
            except Exception as exc:  # noqa: BLE001
                log.exception("Tool %s failed", tool_name)
                tool_calls.append({"name": tool_name, "args": args, "observation": f"Tool error: {exc}"})

        # Synthesize a final answer from the observations.
        summary_messages = list(messages) + [
            Message(role="user", content=self._summarize_prompt(prompt, tool_calls)),
        ]
        final = self.provider.chat(summary_messages)
        return AgentResult(
            final_answer=final.content or "",
            messages=messages,
            tool_calls=tool_calls,
            iterations=len(tool_calls),
        )

    @staticmethod
    def _parse_plan(content: str) -> list[dict[str, Any]]:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            log.warning("Plan was not valid JSON; falling back to empty plan")
            return []
        if not isinstance(parsed, list):
            return []
        return [step for step in parsed if isinstance(step, dict)]

    @staticmethod
    def _summarize_prompt(prompt: str, calls: list[dict[str, Any]]) -> str:
        obs = "\n".join(f"- {c['name']}: {c['observation']}" for c in calls)
        return f"User asked: {prompt}\n\nObservations:\n{obs}\n\nWrite a concise final answer."