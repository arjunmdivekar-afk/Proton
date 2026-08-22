"""Memory tools for agent persistence and recall."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.memory.manager import MemoryManager, memory_manager
from proton.memory.store import MemoryScope


class MemoryAddArgs(BaseModel):
    key: str = Field(description="Short identifier or topic for the memory (e.g. auth_pattern, preferred_test_command)")
    content: str = Field(description="Fact or knowledge to remember")
    scope: str = Field(default="project", description="Scope: 'project', 'user', or 'session'")


class MemoryAddTool(BaseTool):
    name = "memory_add"
    description = "Store a useful fact, architectural rule, or user preference in persistent memory."
    risk_level = RiskLevel.MODIFICATION
    args_schema = MemoryAddArgs

    def __init__(self, manager: Optional[MemoryManager] = None) -> None:
        self.manager = manager or memory_manager

    async def run(self, key: str, content: str, scope: str = "project") -> Dict[str, Any]:
        try:
            mem_scope = MemoryScope(scope.lower())
        except ValueError:
            mem_scope = MemoryScope.PROJECT

        rec = self.manager.remember(key=key, content=content, scope=mem_scope)
        return {
            "success": True,
            "id": rec.id,
            "key": rec.key,
            "scope": rec.scope.value,
            "message": f"Saved fact '{key}' to {rec.scope.value} memory.",
        }


class MemorySearchArgs(BaseModel):
    query: str = Field(description="Keywords to search in stored memories")


class MemorySearchTool(BaseTool):
    name = "memory_search"
    description = "Search saved project rules, preferences, or facts in persistent memory."
    risk_level = RiskLevel.SAFE
    args_schema = MemorySearchArgs

    def __init__(self, manager: Optional[MemoryManager] = None) -> None:
        self.manager = manager or memory_manager

    async def run(self, query: str) -> Dict[str, Any]:
        records = self.manager.recall(query=query)
        formatted = [
            {"id": r.id, "scope": r.scope.value, "key": r.key, "content": r.content}
            for r in records
        ]
        return {"query": query, "count": len(formatted), "memories": formatted}
