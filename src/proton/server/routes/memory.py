"""Categorized Memory API routes with Python client examples."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from proton.server.schemas import MemoryAddRequest, MemorySearchRequest, MemoryItemResponse
from proton.memory.manager import memory_manager
from proton.memory.store import MemoryType

router = APIRouter(prefix="/v1/memory", tags=["Memory"])


def _format_created_at(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt) if dt else datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@router.get(
    "",
    summary="List Categorized Memories",
    response_model=List[MemoryItemResponse],
)
async def list_memories(memory_type: Optional[str] = None):
    """
    List categorized memories stored in SQLite (`~/.proton/knowledge/memory.db`).

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/memory"
    response = requests.get(url, params={"memory_type": "DECISION"})
    memories = response.json()
    for m in memories:
        print(f"- [{m['type']}] #{m['id']}: {m['content']}")
    ```
    """
    t_enum = MemoryType.from_str(memory_type) if memory_type else None
    records = memory_manager.list_all(memory_type=t_enum)
    return [
        MemoryItemResponse(
            id=r.id or 0,
            content=r.content,
            type=r.memory_type.value if hasattr(r.memory_type, "value") else str(r.memory_type),
            confidence=1.0,
            created_at=_format_created_at(r.created_at),
        )
        for r in records
    ]


@router.post(
    "",
    summary="Add Categorized Memory",
    response_model=MemoryItemResponse,
)
async def add_memory(req: MemoryAddRequest):
    """
    Store an explicit memory item categorized under `PROJECT`, `DECISION`, `PREFERENCE`, `FACT`, `TASK`, `USER`, or `SESSION`.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/memory"
    payload = {
        "content": "Prefer single-file implementation for standalone components.",
        "memory_type": "PREFERENCE",
        "confidence": 1.0
    }

    response = requests.post(url, json=payload)
    print("Saved Record:", response.json())
    ```
    """
    t_enum = MemoryType.from_str(req.memory_type)
    record = memory_manager.remember(
        content=req.content,
        memory_type=t_enum,
    )
    return MemoryItemResponse(
        id=record.id or 0,
        content=record.content,
        type=record.memory_type.value if hasattr(record.memory_type, "value") else str(record.memory_type),
        confidence=1.0,
        created_at=_format_created_at(record.created_at),
    )


@router.post(
    "/search",
    summary="Search Categorized Memory",
    response_model=List[MemoryItemResponse],
)
async def search_memories(req: MemorySearchRequest):
    """
    Search stored memories by keyword or semantic phrase.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/memory/search"
    payload = {
        "query": "standalone components",
        "memory_type": "PREFERENCE",
        "limit": 5
    }

    response = requests.post(url, json=payload)
    for m in response.json():
        print(f"Match: {m['content']}")
    ```
    """
    t_enum = MemoryType.from_str(req.memory_type) if req.memory_type else None
    records = memory_manager.recall(query=req.query, memory_type=t_enum)
    return [
        MemoryItemResponse(
            id=r.id or 0,
            content=r.content,
            type=r.memory_type.value if hasattr(r.memory_type, "value") else str(r.memory_type),
            confidence=1.0,
            created_at=_format_created_at(r.created_at),
        )
        for r in records[:req.limit]
    ]


@router.delete(
    "/{memory_id}",
    summary="Delete Memory Record",
)
async def delete_memory(memory_id: int):
    """
    Delete a specific memory record by ID.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    response = requests.delete(f"http://127.0.0.1:8787/v1/memory/1")
    print("Deleted:", response.json())
    ```
    """
    success = memory_manager.forget(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory item {memory_id} not found.")
    return {"status": "deleted", "id": memory_id}


@router.delete(
    "",
    summary="Clear Memories",
)
async def clear_memories(memory_type: Optional[str] = None):
    """
    Clear all memories or memories within a category.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    response = requests.delete("http://127.0.0.1:8787/v1/memory", params={"memory_type": "SESSION"})
    print("Cleared:", response.json())
    ```
    """
    t_enum = MemoryType.from_str(memory_type) if memory_type else None
    count = memory_manager.clear(memory_type=t_enum)
    return {"status": "cleared", "deleted_count": count}
