"""Example Calculator Plugin for Proton."""

from typing import Any, Dict
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.tools.registry import ToolRegistry


class CalculateArgs(BaseModel):
    expression: str = Field(description="Math expression to evaluate, e.g. '42 * 100'")


class CalculateTool(BaseTool):
    name = "calculate"
    description = "Evaluate a mathematical expression safely."
    risk_level = RiskLevel.SAFE
    args_schema = CalculateArgs

    async def run(self, expression: str) -> Dict[str, Any]:
        # Allowed mathematical characters
        allowed_chars = set("0123456789+-*/(). %")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Expression contains invalid characters."}

        try:
            # Safe evaluation of restricted arithmetic expressions
            result = eval(expression, {"__builtins__": {}}, {})
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": f"Evaluation error: {e}"}


def register_tools(registry: ToolRegistry) -> None:
    registry.register(CalculateTool())
