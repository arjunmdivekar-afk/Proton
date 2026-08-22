import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from proton.core.config import get_proton_home
from proton.security.redaction import redact_data


class AuditLogger:
    """Records security, tool execution, model changes, and user decisions into audit db."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or (get_proton_home() / "audit.db")
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    event_type TEXT NOT NULL,
                    tool_name TEXT,
                    risk_level TEXT,
                    decision TEXT,
                    details_json TEXT
                )
                """
            )
            conn.commit()

    def log(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        risk_level: Optional[str] = None,
        decision: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        sanitized_details = redact_data(details or {})
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (timestamp, session_id, event_type, tool_name, risk_level, decision, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    session_id,
                    event_type,
                    tool_name,
                    risk_level,
                    decision,
                    json.dumps(sanitized_details),
                ),
            )
            conn.commit()


# Global audit logger
audit_logger = AuditLogger()
