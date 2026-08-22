"""Base Tool specification and schema definitions for Proton."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, create_model

from proton.core.types import ToolResult, RiskLevel


class BaseTool(ABC):
    """Abstract base class for all deterministic Proton tools."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.SAFE
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool with validated arguments."""
        pass

    def get_json_schema(self) -> Dict[str, Any]:
        """Generate OpenAI/Open-source tool calling function definition."""
        schema: Dict[str, Any] = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

        if self.args_schema:
            model_schema = self.args_schema.model_json_schema()
            schema["function"]["parameters"] = {
                "type": "object",
                "properties": model_schema.get("properties", {}),
                "required": model_schema.get("required", []),
            }

        return schema
