"""Unit tests for configuration manager."""

import pytest
from pathlib import Path
from proton.core.config import ConfigManager, ProtonConfig, SecurityConfig
from proton.core.types import ApprovalPolicy


def test_default_config_loading(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PROTON_HOME", str(tmp_path / ".proton_home"))
    mgr = ConfigManager(workspace_path=tmp_path)
    cfg = mgr.config
    assert isinstance(cfg, ProtonConfig)
    assert cfg.active_connection == "default-lmstudio"
    assert cfg.security.approval_policy == ApprovalPolicy.STRICT


def test_active_connection_update(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PROTON_HOME", str(tmp_path / ".proton_home"))
    mgr = ConfigManager(workspace_path=tmp_path)
    mgr.set_active_connection("my-custom-server")
    assert mgr.config.active_connection == "my-custom-server"

    # Reload from disk
    mgr2 = ConfigManager(workspace_path=tmp_path)
    assert mgr2.config.active_connection == "my-custom-server"
