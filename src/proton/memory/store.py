"""Memory storage schema and SQLite storage manager with explicit categorized memory types."""

import sqlite3
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from proton.core.config import get_proton_home


class MemoryType(str, Enum):
    USER = "USER"
    PROJECT = "PROJECT"
    SESSION = "SESSION"
    PREFERENCE = "PREFERENCE"
    FACT = "FACT"
    DECISION = "DECISION"
    TASK = "TASK"

    @classmethod
    def from_str(cls, val: str) -> "MemoryType":
        clean = val.strip().upper()
        for member in cls:
            if member.value == clean or member.name == clean:
                return member
        return cls.PROJECT


# Backward compatibility alias
MemoryScope = MemoryType


class MemoryRecord(BaseModel):
    id: Optional[int] = None
    memory_type: MemoryType = MemoryType.PROJECT
    key: str = ""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def scope(self) -> MemoryType:
        return self.memory_type


class MemoryStore:
    """Stores structured and categorized memory records in SQLite."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or (get_proton_home() / "memory.db")
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_type TEXT NOT NULL,
                    key TEXT,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Add migration check if column was previously called scope
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(memories)")
            cols = [c[1] for c in cur.fetchall()]
            if "scope" in cols and "memory_type" not in cols:
                conn.execute("ALTER TABLE memories RENAME COLUMN scope TO memory_type")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_key ON memories(key)")
            conn.commit()

    def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.PROJECT,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        scope: Optional[Any] = None,  # Backward compatibility
    ) -> MemoryRecord:
        m_type = memory_type
        if scope is not None:
            if isinstance(scope, MemoryType):
                m_type = scope
            elif isinstance(scope, str):
                m_type = MemoryType.from_str(scope)

        item_key = key or ""
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (memory_type, key, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (m_type.value, item_key, content, meta_json, now),
            )
            conn.commit()
            rec_id = cursor.lastrowid

        return MemoryRecord(
            id=rec_id,
            memory_type=m_type,
            key=item_key,
            content=content,
            metadata=metadata or {},
        )

    def list_memories(self, memory_type: Optional[MemoryType] = None, scope: Optional[Any] = None) -> List[MemoryRecord]:
        m_type = memory_type
        if scope is not None and m_type is None:
            m_type = scope if isinstance(scope, MemoryType) else MemoryType.from_str(str(scope))

        query = "SELECT id, memory_type, key, content, metadata_json, created_at FROM memories"
        params = ()
        if m_type:
            query += " WHERE memory_type = ?"
            params = (m_type.value,)
        query += " ORDER BY id DESC"

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append(
                MemoryRecord(
                    id=r[0],
                    memory_type=MemoryType.from_str(r[1]),
                    key=r[2] or "",
                    content=r[3],
                    metadata=json.loads(r[4] or "{}"),
                    created_at=datetime.fromisoformat(r[5]),
                )
            )
        return results

    def search(self, query: str, memory_type: Optional[MemoryType] = None, scope: Optional[Any] = None) -> List[MemoryRecord]:
        all_recs = self.list_memories(memory_type=memory_type, scope=scope)
        terms = query.lower().split()
        if not terms:
            return all_recs[:15]

        matched = []
        for rec in all_recs:
            text = f"{rec.memory_type.value} {rec.key} {rec.content}".lower()
            if any(term in text for term in terms):
                matched.append(rec)
        return matched

    def delete(self, record_id: int) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self, memory_type: Optional[MemoryType] = None, scope: Optional[Any] = None) -> int:
        m_type = memory_type
        if scope is not None and m_type is None:
            m_type = scope if isinstance(scope, MemoryType) else MemoryType.from_str(str(scope))

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            if m_type:
                cursor.execute("DELETE FROM memories WHERE memory_type = ?", (m_type.value,))
            else:
                cursor.execute("DELETE FROM memories")
            conn.commit()
            return cursor.rowcount
