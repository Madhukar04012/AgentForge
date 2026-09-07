"""Tests for the tool implementations."""

from __future__ import annotations

import pytest

from agentforge.tools.base import ToolContext
from agentforge.tools.builtin.calculator import CalculatorTool
from agentforge.tools.builtin.http import HttpGetTool
from agentforge.tools.builtin.filesystem import ReadFileTool, WriteFileTool


def test_calculator_basic() -> None:
    t = CalculatorTool()
    r = t.run({"expression": "2 + 3 * 4"}, ToolContext())
    assert r.ok
    assert r.output == 14


def test_calculator_rejects_empty() -> None:
    t = CalculatorTool()
    r = t.run({"expression": "   "}, ToolContext())
    assert not r.ok
    assert "non-empty" in (r.error or "")


def test_calculator_rejects_unsafe() -> None:
    t = CalculatorTool()
    r = t.run({"expression": "__import__('os').system('echo hi')"}, ToolContext())
    assert not r.ok


def test_http_get_rejects_non_url(tmp_path) -> None:
    t = HttpGetTool()
    r = t.run({"url": "file:///etc/passwd"}, ToolContext())
    assert not r.ok


def test_filesystem_read_write(tmp_path) -> None:
    w = WriteFileTool(root=tmp_path)
    r = w.run({"path": "hello.txt", "contents": "hi"}, ToolContext())
    assert r.ok

    rd = ReadFileTool(root=tmp_path)
    r2 = rd.run({"path": "hello.txt"}, ToolContext())
    assert r2.ok
    assert r2.output == "hi"


def test_filesystem_read_missing(tmp_path) -> None:
    rd = ReadFileTool(root=tmp_path)
    r = rd.run({"path": "nope.txt"}, ToolContext())
    assert not r.ok


def test_filesystem_write_typecheck(tmp_path) -> None:
    w = WriteFileTool(root=tmp_path)
    r = w.run({"path": "x.txt", "contents": 123}, ToolContext())
    assert not r.ok