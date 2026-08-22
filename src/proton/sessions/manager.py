"""Session Manager handling SQLite conversation persistence, resume, and export."""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from proton.core.config import get_proton_home
from proton.core.types import Message, Role
from proton.sessions.models import SessionSummary, SessionDetail


class SessionManager:
    """Manages persistent chat sessions in SQLite database."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or (get_proton_home() / "proton.db")
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    workspace_path TEXT NOT NULL,
                    connection_id TEXT,
                    model_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    name TEXT,
                    tool_calls_json TEXT,
                    tool_call_id TEXT,
                    metadata_json TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON session_messages(session_id)")
            conn.commit()

    def create_session(
        self,
        workspace_path: str,
        title: str = "New Session",
        connection_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> SessionDetail:
        sid = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO sessions (id, title, workspace_path, connection_id, model_id, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, title, workspace_path, connection_id, model_id, now, now, "{}"),
            )
            conn.commit()

        return SessionDetail(
            id=sid,
            title=title,
            workspace_path=workspace_path,
            connection_id=connection_id,
            model_id=model_id,
        )

    def append_message(self, session_id: str, message: Message) -> None:
        now = datetime.now(timezone.utc).isoformat()
        tc_json = json.dumps(message.tool_calls) if message.tool_calls else None
        meta_json = json.dumps(message.metadata) if message.metadata else None

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO session_messages (session_id, role, content, name, tool_calls_json, tool_call_id, metadata_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    message.role.value,
                    message.content,
                    message.name,
                    tc_json,
                    message.tool_call_id,
                    meta_json,
                    now,
                ),
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            conn.commit()

    def get_session(self, session_id: str) -> Optional[SessionDetail]:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, title, workspace_path, connection_id, model_id, created_at, updated_at, metadata_json FROM sessions WHERE id = ?", (session_id,))
            srow = cur.fetchone()
            if not srow:
                return None

            cur.execute(
                """
                SELECT role, content, name, tool_calls_json, tool_call_id, metadata_json, timestamp 
                FROM session_messages WHERE session_id = ? ORDER BY id ASC
                """,
                (session_id,),
            )
            mrows = cur.fetchall()

        messages: List[Message] = []
        for mr in mrows:
            tc = json.loads(mr[3]) if mr[3] else None
            meta = json.loads(mr[5]) if mr[5] else {}
            messages.append(
                Message(
                    role=Role(mr[0]),
                    content=mr[1],
                    name=mr[2],
                    tool_calls=tc,
                    tool_call_id=mr[4],
                    metadata=meta,
                    timestamp=datetime.fromisoformat(mr[6]),
                )
            )

        return SessionDetail(
            id=srow[0],
            title=srow[1],
            workspace_path=srow[2],
            connection_id=srow[3],
            model_id=srow[4],
            created_at=datetime.fromisoformat(srow[5]),
            updated_at=datetime.fromisoformat(srow[6]),
            metadata=json.loads(srow[7] or "{}"),
            messages=messages,
        )

    def list_sessions(self, limit: int = 20) -> List[SessionSummary]:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.id, s.title, s.created_at, s.updated_at, s.model_id, s.connection_id, COUNT(m.id)
                FROM sessions s
                LEFT JOIN session_messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()

        return [
            SessionSummary(
                id=r[0],
                title=r[1],
                created_at=datetime.fromisoformat(r[2]),
                updated_at=datetime.fromisoformat(r[3]),
                model_id=r[4],
                connection_id=r[5],
                message_count=r[6],
            )
            for r in rows
        ]

    def get_latest_session(self) -> Optional[SessionDetail]:
        sessions = self.list_sessions(limit=1)
        if sessions:
            return self.get_session(sessions[0].id)
        return None

    def export_markdown(self, session_id: str) -> str:
        session = self.get_session(session_id)
        if not session:
            return ""

        lines = [
            f"# Session: {session.title}",
            f"- **Session ID**: `{session.id}`",
            f"- **Model**: `{session.model_id or 'default'}`",
            f"- **Created**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Workspace**: `{session.workspace_path}`",
            "",
            "---",
            "",
        ]

        for m in session.messages:
            lines.append(f"### {m.role.value.upper()}")
            lines.append(m.content)
            if m.tool_calls:
                lines.append("```json")
                lines.append(json.dumps(m.tool_calls, indent=2))
                lines.append("```")
            lines.append("")

        return "\n".join(lines)
