"""Test suite for Proton hardware device configuration (proton set --CPU / --GPU / --Partial)."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from proton.cli.app import app
from proton.core.config import ConfigManager
from proton.cli.set_cmd import set_hardware_mode
from proton.providers.transformers import TransformersProvider

runner = CliRunner()


def test_cli_set_cpu():
    """Verify proton set --CPU sets mode to cpu."""
    result = runner.invoke(app, ["set", "--CPU"])
    assert result.exit_code == 0
    assert "Hardware Execution Mode set to CPU" in result.stdout

    config = ConfigManager().config
    assert config.device_mode == "cpu"


def test_cli_set_gpu():
    """Verify proton set --GPU sets mode to gpu."""
    result = runner.invoke(app, ["set", "--GPU"])
    assert result.exit_code == 0
    assert "Hardware Execution Mode set to GPU" in result.stdout

    config = ConfigManager().config
    assert config.device_mode == "gpu"


def test_cli_set_partial():
    """Verify proton set --Partial sets mode to partial."""
    result = runner.invoke(app, ["set", "--Partial"])
    assert result.exit_code == 0
    assert "Hardware Execution Mode set to PARTIAL" in result.stdout

    config = ConfigManager().config
    assert config.device_mode == "partial"


def test_cli_set_positional():
    """Verify positional mode syntax works."""
    result = runner.invoke(app, ["set", "cpu"])
    assert result.exit_code == 0
    assert "Hardware Execution Mode set to CPU" in result.stdout
    assert ConfigManager().config.device_mode == "cpu"


def test_cli_set_status_display():
    """Verify proton set with no args displays status table."""
    result = runner.invoke(app, ["set"])
    assert result.exit_code == 0
    assert "HARDWARE INFERENCE CONFIGURATION" in result.stdout
    assert "Active Execution Mode" in result.stdout


def test_transformers_provider_respects_device_mode():
    """Verify TransformersProvider checks configured device_mode correctly."""
    # Test CPU mode
    with patch("proton.core.config.ConfigManager.config") as mock_cfg:
        mock_cfg.device_mode = "cpu"
        p_cpu = TransformersProvider()
        assert p_cpu.device is None

    # Test GPU mode
    with patch("proton.core.config.ConfigManager.config") as mock_cfg:
        mock_cfg.device_mode = "gpu"
        p_gpu = TransformersProvider()
        assert p_gpu.device is None
