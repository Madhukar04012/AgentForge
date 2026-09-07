"""Tests for providers."""

from __future__ import annotations

import pytest

from agentforge.providers.base import ChatResponse, Message
from agentforge.providers.mock import MockProvider
from agentforge.providers.openai_provider import OpenAIProvider
from agentforge.providers.anthropic_provider import AnthropicProvider


def test_mock_returns_first_then_default() -> None:
    p = MockProvider(
        scripted=[ChatResponse(content="first"), ChatResponse(content="second")],
        default="fallback",
    )
    assert p.chat([]).content == "first"
    assert p.chat([]).content == "second"
    assert p.chat([]).content == "fallback"


def test_openai_requires_key() -> None:
    p = OpenAIProvider(api_key=None)
    # Force-ensure the env var isn't accidentally set in the test process.
    p.api_key = None
    with pytest.raises(RuntimeError):
        p.chat([Message(role="user", content="hi")])


def test_anthropic_requires_key() -> None:
    p = AnthropicProvider(api_key=None)
    p.api_key = None
    with pytest.raises(RuntimeError):
        p.chat([Message(role="user", content="hi")])


def test_openai_picks_up_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    p = OpenAIProvider()
    assert p.api_key == "test-key"