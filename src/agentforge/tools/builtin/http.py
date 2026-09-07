"""HTTP GET tool."""

from __future__ import annotations

from typing import Any

import httpx

from agentforge.tools.base import Tool, ToolContext, ToolResult


class HttpGetTool(Tool):
    name = "http_get"
    description = "Fetch the contents of a URL via HTTP GET and return the response body."

    def __init__(self, timeout: float = 10.0, max_bytes: int = 1_000_000) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        url = args.get("url", "")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return ToolResult(output=None, error="url must be an http(s) URL")
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                resp = client.get(url)
        except httpx.HTTPError as exc:
            return ToolResult(output=None, error=f"http error: {exc}")

        body = resp.content[: self.max_bytes].decode("utf-8", errors="replace")
        return ToolResult(output={"status": resp.status_code, "body": body})