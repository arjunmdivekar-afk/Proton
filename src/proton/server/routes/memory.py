"""Categorized Memory API routes."""

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


@router.get("", response_model=List[MemoryItemResponse])
async def list_memories(memory_type: Optional[str] = None):
    """List categorized memories, optionally filtered by type."""
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


@router.post("", response_model=MemoryItemResponse)
async def add_memory(req: MemoryAddRequest):
    """Add a structured memory item (PROJECT, DECISION, PREFERENCE, FACT, TASK, USER, SESSION)."""
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


@router.post("/search", response_model=List[MemoryItemResponse])
async def search_memories(req: MemorySearchRequest):
    """Search categorized memories by keyword or semantic query."""
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


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a memory item by ID."""
    success = memory_manager.forget(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory item {memory_id} not found.")
    return {"status": "deleted", "id": memory_id}


@router.delete("")
async def clear_memories(memory_type: Optional[str] = None):
    """Clear memories (by category or all)."""
    t_enum = MemoryType.from_str(memory_type) if memory_type else None
    count = memory_manager.clear(memory_type=t_enum)
    return {"status": "cleared", "deleted_count": count}
