"""Memory tools for agent persistence and recall."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.memory.manager import MemoryManager, memory_manager
from proton.memory.store import MemoryType


class MemoryAddArgs(BaseModel):
    content: str = Field(description="Fact, decision, preference, or rule to remember")
    memory_type: str = Field(
        default="PROJECT",
        description="Category: 'USER', 'PROJECT', 'SESSION', 'PREFERENCE', 'FACT', 'DECISION', or 'TASK'",
    )
    key: Optional[str] = Field(default=None, description="Optional short identifier or topic")


class MemoryAddTool(BaseTool):
    name = "memory_add"
    description = "Store a useful fact, architectural decision, user preference, or project rule in categorized persistent memory."
    risk_level = RiskLevel.MODIFICATION
    args_schema = MemoryAddArgs

    def __init__(self, manager: Optional[MemoryManager] = None) -> None:
        self.manager = manager or memory_manager

    async def run(self, content: str, memory_type: str = "PROJECT", key: Optional[str] = None) -> Dict[str, Any]:
        m_type = MemoryType.from_str(memory_type)
        rec = self.manager.remember(content=content, memory_type=m_type, key=key)
        return {
            "success": True,
            "id": rec.id,
            "type": rec.memory_type.value,
            "key": rec.key,
            "content": rec.content,
            "message": f"Saved {rec.memory_type.value} memory item (ID: {rec.id}).",
        }


class MemorySearchArgs(BaseModel):
    query: str = Field(description="Keywords to search in stored memories")
    memory_type: Optional[str] = Field(default=None, description="Optional category filter")


class MemorySearchTool(BaseTool):
    name = "memory_search"
    description = "Search saved project rules, preferences, decisions, or facts in persistent memory."
    risk_level = RiskLevel.SAFE
    args_schema = MemorySearchArgs

    def __init__(self, manager: Optional[MemoryManager] = None) -> None:
        self.manager = manager or memory_manager

    async def run(self, query: str, memory_type: Optional[str] = None) -> Dict[str, Any]:
        m_type = MemoryType.from_str(memory_type) if memory_type else None
        records = self.manager.recall(query=query, memory_type=m_type)
        formatted = [
            {"id": r.id, "type": r.memory_type.value, "key": r.key, "content": r.content}
            for r in records
        ]
        return {"query": query, "count": len(formatted), "memories": formatted}
