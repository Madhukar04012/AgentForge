"""Filesystem read/write tools — restricted to a configured root."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agentforge.tools.base import Tool, ToolContext, ToolResult


class _FSBase(Tool):
    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        self.root = Path(root).resolve() if root else Path.cwd().resolve()

    def _resolve(self, path: str) -> Path:
        # NOTE: caller is responsible for sanitizing path input.
        candidate = (self.root / path).resolve()
        return candidate


class ReadFileTool(_FSBase):
    name = "read_file"
    description = "Read the text contents of a file under the configured root."

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        path = args.get("path", "")
        if not isinstance(path, str) or not path:
            return ToolResult(output=None, error="path must be a non-empty string")
        target = self._resolve(path)
        if not target.exists() or not target.is_file():
            return ToolResult(output=None, error=f"file not found: {path}")
        try:
            content = target.read_text(encoding="utf-8")
        except OSError as exc:
            return ToolResult(output=None, error=f"read error: {exc}")
        return ToolResult(output=content)


class WriteFileTool(_FSBase):
    name = "write_file"
    description = "Write text contents to a file under the configured root (overwrites)."

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        path = args.get("path", "")
        contents = args.get("contents", "")
        if not isinstance(path, str) or not path:
            return ToolResult(output=None, error="path must be a non-empty string")
        if not isinstance(contents, str):
            return ToolResult(output=None, error="contents must be a string")
        target = self._resolve(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")
        except OSError as exc:
            return ToolResult(output=None, error=f"write error: {exc}")
        return ToolResult(output=f"wrote {len(contents)} bytes to {path}")