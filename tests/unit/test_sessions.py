"""Unit tests for session manager and persistence."""

import pytest
from pathlib import Path
from proton.sessions.manager import SessionManager
from proton.core.types import Message, Role


def test_session_creation_and_messages(tmp_path: Path):
    db_path = tmp_path / "proton_test.db"
    mgr = SessionManager(db_path)

    sess = mgr.create_session(
        workspace_path=str(tmp_path),
        title="Test Coding Task",
        connection_id="default-lmstudio",
        model_id="qwen3.5-4b",
    )
    assert sess.id.startswith("sess_")

    # Add message
    msg = Message(role=Role.USER, content="Please fix the bug in auth.py")
    mgr.append_message(sess.id, msg)

    loaded = mgr.get_session(sess.id)
    assert loaded is not None
    assert len(loaded.messages) == 1
    assert loaded.messages[0].content == "Please fix the bug in auth.py"

    # Export markdown
    md = mgr.export_markdown(sess.id)
    assert "Test Coding Task" in md
    assert "Please fix the bug" in md
