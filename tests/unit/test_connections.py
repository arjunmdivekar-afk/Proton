"""Unit tests for connection schema, probe, and manager."""

import pytest
from pathlib import Path
from proton.connection.schema import ConnectionProfile, ProviderType, ConnectionStatus, ConnectionTestResult
from proton.connection.manager import ConnectionManager
from proton.core.config import ConfigManager


def test_connection_profile_base_url():
    # Local default
    p1 = ConnectionProfile(
        id="local-lm",
        name="Local LM",
        provider=ProviderType.LMSTUDIO,
        host="127.0.0.1",
        port=1234,
        protocol="http",
        base_path="/v1",
    )
    assert p1.base_url == "http://127.0.0.1:1234/v1"
    assert p1.is_local is True

    # Remote LAN IP
    p2 = ConnectionProfile(
        id="lan-lm",
        name="LAN LM Studio",
        provider=ProviderType.LMSTUDIO,
        host="192.168.1.50",
        port=1234,
        protocol="http",
        base_path="/v1",
    )
    assert p2.base_url == "http://192.168.1.50:1234/v1"
    assert p2.is_local is False


def test_connection_manager_crud(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PROTON_HOME", str(tmp_path / ".proton"))
    cfg_mgr = ConfigManager(workspace_path=tmp_path)
    mgr = ConnectionManager(cfg_mgr)

    # Initial defaults
    conns = mgr.list_connections()
    assert len(conns) >= 2
    assert any(c.provider == ProviderType.LMSTUDIO for c in conns)
    assert any(c.provider == ProviderType.OLLAMA for c in conns)

    # Add LAN profile
    lan_profile = ConnectionProfile(
        id="office-pc",
        name="Office LM Studio",
        provider=ProviderType.LMSTUDIO,
        host="192.168.1.50",
        port=1234,
    )
    mgr.add_connection(lan_profile)
    assert mgr.get_connection("office-pc") is not None

    # Switch active
    assert mgr.set_active_connection("office-pc") is True
    assert mgr.get_active_connection().id == "office-pc"

    # Remove
    assert mgr.remove_connection("office-pc") is True
    assert mgr.get_connection("office-pc") is None
