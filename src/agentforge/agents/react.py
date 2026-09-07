"""A simple ReAct-style agent loop."""

from __future__ import annotations

import json
import logging
from typing import Any

from agentforge.agents.base import Agent, AgentResult
from agentforge.providers.base import Message
from agentforge.tools.base import ToolContext

log = logging.getLogger(__name__)


class ReActAgent(Agent):
    """Reason/Act loop: think, decide on a tool, call it, observe, repeat."""

    def run(self, prompt: str) -> AgentResult:
        messages: list[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt),
        ]
        tool_calls: list[dict[str, Any]] = []
        iterations = 0
        ctx = ToolContext()

        for _ in range(self.max_iterations):
            iterations += 1
            response = self.provider.chat(messages, tools=self.tools.schemas())

            # If the model didn't ask for a tool, treat the content as the final answer.
            if not response.tool_calls:
                return AgentResult(
                    final_answer=response.content or "",
                    messages=messages + [Message(role="assistant", content=response.content or "")],
                    tool_calls=tool_calls,
                    iterations=iterations,
                )

            # Append the assistant's tool-call turn to the transcript.
            messages.append(
                Message(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                )
            )

            for call in response.tool_calls:
                name = call.get("name")
                args = call.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                tool = self.tools.get(name) if name else None
                if tool is None:
                    observation = f"Unknown tool: {name!r}"
                else:
                    try:
                        result = tool.run(args, ctx)
                        observation = result.output
                    except Exception as exc:  # noqa: BLE001 — surfaced as observation
                        log.exception("Tool %s failed", name)
                        observation = f"Tool error: {exc}"

                tool_calls.append({"name": name, "args": args, "observation": observation})
                messages.append(Message(role="tool", name=name, content=str(observation)))

        # Hit the iteration cap — return whatever we have.
        last = messages[-1] if messages else None
        return AgentResult(
            final_answer=last.content if last and last.role == "assistant" else "",
            messages=messages,
            tool_calls=tool_calls,
            iterations=iterations,
        )