"""Tool abstractions and registry."""

from agentforge.tools.base import Tool, ToolContext, ToolResult
from agentforge.tools.registry import ToolRegistry
from agentforge.tools.builtin.calculator import CalculatorTool
from agentforge.tools.builtin.http import HttpGetTool
from agentforge.tools.builtin.filesystem import ReadFileTool, WriteFileTool

__all__ = [
    "Tool",
    "ToolContext",
    "ToolResult",
    "ToolRegistry",
    "CalculatorTool",
    "HttpGetTool",
    "ReadFileTool",
    "WriteFileTool",
]