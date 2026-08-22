"""Plugin discovery and dynamic loader."""

import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Optional

from proton.plugins.manifest import PluginManifest
from proton.tools.registry import ToolRegistry
from proton.core.config import get_proton_home
from proton.core.exceptions import PluginError


class PluginLoader:
    """Discovers, validates manifests, and loads external plugins."""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry
        self.home_plugins_dir = get_proton_home() / "plugins"
        self.home_plugins_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_plugins: Dict[str, PluginManifest] = {}

    def discover_and_load_all(self, workspace_path: Optional[Path] = None) -> List[PluginManifest]:
        """Scan ~/.proton/plugins and ./.proton/plugins."""
        plugin_dirs = [self.home_plugins_dir]
        if workspace_path:
            local_plugins = workspace_path / ".proton" / "plugins"
            if local_plugins.exists():
                plugin_dirs.append(local_plugins)

        loaded = []
        for pdir in plugin_dirs:
            if not pdir.exists():
                continue
            for item in pdir.iterdir():
                if item.is_dir() and (item / "manifest.json").exists():
                    manifest = self.load_plugin(item)
                    if manifest:
                        loaded.append(manifest)
        return loaded

    def load_plugin(self, plugin_dir: Path) -> Optional[PluginManifest]:
        manifest_file = plugin_dir / "manifest.json"
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            manifest = PluginManifest(**data)
        except Exception as e:
            return None

        entry_file = plugin_dir / manifest.entrypoint
        if not entry_file.exists():
            return None

        # Dynamically import module
        try:
            spec = importlib.util.spec_from_file_location(f"proton_plugin_{manifest.name}", entry_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # If module has a register_tools function
                if hasattr(module, "register_tools"):
                    module.register_tools(self.tool_registry)

                self._loaded_plugins[manifest.name] = manifest
                return manifest
        except Exception:
            return None

        return manifest
