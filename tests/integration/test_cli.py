"""Integration tests for Proton CLI."""

import pytest
from typer.testing import CliRunner
from proton.cli.app import app
import proton

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert proton.__version__ in result.stdout


def test_cli_connection_list():
    result = runner.invoke(app, ["connection", "list"])
    assert result.exit_code == 0
    assert "Proton AI Connections" in result.stdout


def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "DIAGNOSTICS" in result.stdout


def test_cli_rag_status():
    result = runner.invoke(app, ["rag", "status"])
    assert result.exit_code == 0
    assert "RAG Store Database" in result.stdout
