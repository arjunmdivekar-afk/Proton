"""Unit test for ProtonREPL component."""

from pathlib import Path
import pytest
from proton.tui.repl import ProtonREPL
from proton.core.types import Message, Role


def test_repl_initialization(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PROTON_HOME", str(tmp_path / ".proton_home"))
    repl = ProtonREPL(workspace_path=tmp_path)
    assert repl.workspace_path == tmp_path
    assert repl.current_session is not None
    repl.print_banner()
