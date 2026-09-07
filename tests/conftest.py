"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from agentforge.providers.base import ChatResponse
from agentforge.providers.mock import MockProvider
from agentforge.tools.registry import ToolRegistry
from agentforge.tools.builtin.calculator import CalculatorTool


@pytest.fixture
def registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(CalculatorTool())
    return r


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider(scripted=[ChatResponse(content="hello")])


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    from agentforge.config.settings import get_settings

    get_settings.cache_clear()