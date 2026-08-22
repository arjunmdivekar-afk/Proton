"""Memory Manager orchestrating session, project, and user level memory."""

from typing import Dict, List, Optional
from proton.memory.store import MemoryStore, MemoryScope, MemoryRecord


class MemoryManager:
    """Manages memory retrieval and persistence across all scopes."""

    def __init__(self, store: Optional[MemoryStore] = None) -> None:
        self.store = store or MemoryStore()

    def remember(self, key: str, content: str, scope: MemoryScope = MemoryScope.PROJECT, metadata: Optional[Dict[str, str]] = None) -> MemoryRecord:
        return self.store.add(scope=scope, key=key, content=content, metadata=metadata)

    def recall(self, query: str, scope: Optional[MemoryScope] = None) -> List[MemoryRecord]:
        return self.store.search(query=query, scope=scope)

    def list_all(self, scope: Optional[MemoryScope] = None) -> List[MemoryRecord]:
        return self.store.list_memories(scope=scope)

    def forget(self, record_id: int) -> bool:
        return self.store.delete(record_id)


# Singleton instance
memory_manager = MemoryManager()
