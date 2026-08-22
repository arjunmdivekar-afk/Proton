"""Memory Manager orchestrating categorized project, user, preference, and decision memory."""

from typing import Any, Dict, List, Optional
from proton.memory.store import MemoryStore, MemoryType, MemoryScope, MemoryRecord


class MemoryManager:
    """Manages categorized memory persistence and retrieval across all explicit types."""

    def __init__(self, store: Optional[MemoryStore] = None) -> None:
        self.store = store or MemoryStore()

    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.PROJECT,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scope: Optional[Any] = None,
    ) -> MemoryRecord:
        return self.store.add(
            content=content,
            memory_type=memory_type,
            key=key,
            metadata=metadata,
            scope=scope,
        )

    def recall(self, query: str, memory_type: Optional[MemoryType] = None, scope: Optional[Any] = None) -> List[MemoryRecord]:
        return self.store.search(query=query, memory_type=memory_type, scope=scope)

    def list_all(self, memory_type: Optional[MemoryType] = None, scope: Optional[Any] = None) -> List[MemoryRecord]:
        return self.store.list_memories(memory_type=memory_type, scope=scope)

    def forget(self, record_id: int) -> bool:
        return self.store.delete(record_id)

    def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        return self.store.clear(memory_type=memory_type)


# Singleton instance
memory_manager = MemoryManager()
