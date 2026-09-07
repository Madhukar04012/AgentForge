"""Tests for the agent implementations."""

from __future__ import annotations

from agentforge.agents.react import ReActAgent
from agentforge.providers.base import ChatResponse
from agentforge.providers.mock import MockProvider


def test_react_returns_final_answer_when_no_tool_called(registry, monkeypatch) -> None:
    provider = MockProvider(scripted=[ChatResponse(content="the answer is 42")])
    agent = ReActAgent(provider=provider, tools=registry)
    result = agent.run("what is the meaning of life?")
    assert result.final_answer == "the answer is 42"
    assert result.iterations == 1
    assert result.tool_calls == []


def test_react_calls_tool_then_answers(registry) -> None:
    provider = MockProvider(
        scripted=[
            ChatResponse(content="thinking", tool_calls=[{"name": "calculator", "arguments": {"expression": "2+2"}}]),
            ChatResponse(content="4"),
        ]
    )
    agent = ReActAgent(provider=provider, tools=registry)
    result = agent.run("2 + 2")
    assert result.final_answer == "4"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["name"] == "calculator"


def test_react_handles_unknown_tool_gracefully(registry) -> None:
    provider = MockProvider(
        scripted=[
            ChatResponse(content="", tool_calls=[{"name": "nope", "arguments": {}}]),
            ChatResponse(content="done"),
        ]
    )
    agent = ReActAgent(provider=provider, tools=registry, max_iterations=3)
    result = agent.run("x")
    assert any("Unknown tool" in str(c.get("observation", "")) for c in result.tool_calls)