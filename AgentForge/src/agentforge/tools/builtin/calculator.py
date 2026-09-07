"""Calculator tool — safely evaluates arithmetic expressions."""

from __future__ import annotations

import ast
import operator
from typing import Any

from agentforge.tools.base import Tool, ToolContext, ToolResult


_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluate a basic arithmetic expression and return the numeric result."

    def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        expression = args.get("expression", "")
        if not isinstance(expression, str) or not expression.strip():
            return ToolResult(output=None, error="expression must be a non-empty string")
        try:
            value = _safe_eval(expression)
        except (SyntaxError, ValueError, ZeroDivisionError, TypeError) as exc:
            return ToolResult(output=None, error=f"evaluation failed: {exc}")
        return ToolResult(output=value)


def _safe_eval(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError(f"unsupported constant: {node.value!r}")
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _BIN_OPS:
                raise TypeError(f"unsupported operator: {op_type.__name__}")
            return _BIN_OPS[op_type](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _UNARY_OPS:
                raise TypeError(f"unsupported unary operator: {op_type.__name__}")
            return _UNARY_OPS[op_type](_eval(node.operand))
        raise TypeError(f"unsupported node: {type(node).__name__}")

    return _eval(tree)