"""Unit tests for plugin discovery and manifest loading."""

import json
import pytest
from pathlib import Path
from proton.plugins.manifest import PluginManifest
from proton.plugins.loader import PluginLoader
from proton.tools.registry import ToolRegistry


def test_plugin_manifest_validation():
    data = {
        "name": "calc-plugin",
        "version": "1.0.0",
        "description": "Calculator plugin for Proton",
        "entrypoint": "plugin.py",
        "permissions": ["math.eval"],
    }
    manifest = PluginManifest(**data)
    assert manifest.name == "calc-plugin"
    assert manifest.version == "1.0.0"


def test_plugin_loader(tmp_path: Path):
    plugin_dir = tmp_path / "calc"
    plugin_dir.mkdir(parents=True)

    manifest_data = {
        "name": "calc",
        "version": "0.1.0",
        "description": "Simple Calc",
        "entrypoint": "plugin.py",
    }
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    plugin_code = """
from proton.tools.base import BaseTool
from proton.core.types import RiskLevel

class AddTool(BaseTool):
    name = "add_numbers"
    description = "Add two numbers"
    risk_level = RiskLevel.SAFE

    async def run(self, a: int, b: int):
        return {"result": a + b}

def register_tools(registry):
    registry.register(AddTool())
"""
    (plugin_dir / "plugin.py").write_text(plugin_code, encoding="utf-8")

    registry = ToolRegistry()
    loader = PluginLoader(registry)
    manifest = loader.load_plugin(plugin_dir)

    assert manifest is not None
    assert manifest.name == "calc"
    assert registry.get_tool("add_numbers") is not None
