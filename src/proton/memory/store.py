"""Memory storage schema and SQLite storage manager."""

import sqlite3
import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from proton.core.config import get_proton_home


class MemoryScope(str, Enum):
    SESSION = "session"
    PROJECT = "project"
    USER = "user"


class MemoryRecord(BaseModel):
    id: Optional[int] = None
    scope: MemoryScope = MemoryScope.PROJECT
    key: str
    content: str
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryStore:
    """Stores structured memory items in SQLite."""

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
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_scope ON memories(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_key ON memories(key)")
            conn.commit()

    def add(self, scope: MemoryScope, key: str, content: str, metadata: Optional[Dict[str, str]] = None) -> MemoryRecord:
        now = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (scope, key, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (scope.value, key, content, meta_json, now),
            )
            conn.commit()
            rec_id = cursor.lastrowid

        return MemoryRecord(
            id=rec_id,
            scope=scope,
            key=key,
            content=content,
            metadata=metadata or {},
        )

    def list_memories(self, scope: Optional[MemoryScope] = None) -> List[MemoryRecord]:
        query = "SELECT id, scope, key, content, metadata_json, created_at FROM memories"
        params = ()
        if scope:
            query += " WHERE scope = ?"
            params = (scope.value,)
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
                    scope=MemoryScope(r[1]),
                    key=r[2],
                    content=r[3],
                    metadata=json.loads(r[4] or "{}"),
                    created_at=datetime.fromisoformat(r[5]),
                )
            )
        return results

    def search(self, query: str, scope: Optional[MemoryScope] = None) -> List[MemoryRecord]:
        all_recs = self.list_memories(scope)
        terms = query.lower().split()
        if not terms:
            return all_recs[:10]

        matched = []
        for rec in all_recs:
            text = f"{rec.key} {rec.content}".lower()
            if any(term in text for term in terms):
                matched.append(rec)
        return matched

    def delete(self, record_id: int) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self, scope: Optional[MemoryScope] = None) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            if scope:
                cursor.execute("DELETE FROM memories WHERE scope = ?", (scope.value,))
            else:
                cursor.execute("DELETE FROM memories")
            conn.commit()
            return cursor.rowcount
