"""Tests for the tool registry."""

from __future__ import annotations

import pytest

from agentforge.tools.registry import ToolRegistry
from agentforge.tools.builtin.calculator import CalculatorTool


def test_register_and_get() -> None:
    r = ToolRegistry()
    t = CalculatorTool()
    r.register(t)
    assert r.get("calculator") is t


def test_register_duplicate_raises() -> None:
    r = ToolRegistry()
    r.register(CalculatorTool())
    with pytest.raises(ValueError):
        r.register(CalculatorTool())


def test_register_rejects_empty_name() -> None:
    class Bad:
        name = ""

    r = ToolRegistry()
    with pytest.raises(ValueError):
        r.register(Bad())


def test_unregister() -> None:
    r = ToolRegistry()
    t = CalculatorTool()
    r.register(t)
    r.unregister(t.name)
    assert t.name not in r


def test_schemas_returns_list_of_dicts() -> None:
    r = ToolRegistry()
    r.register(CalculatorTool())
    schemas = r.schemas()
    assert isinstance(schemas, list)
    assert schemas[0]["name"] == "calculator"