"""Connection Manager to handle multiple AI endpoints, profiles, and model discovery."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import yaml

from proton.connection.schema import ConnectionProfile, ConnectionStatus, ConnectionTestResult, ProviderType
from proton.connection.probe import probe_connection
from proton.core.types import ModelInfo, ModelCapabilities
from proton.core.config import get_proton_home, ConfigManager


class ConnectionManager:
    """Manages AI provider connections (LM Studio, Ollama, OpenAI-compatible)."""

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        self.config_mgr = config_manager or ConfigManager()
        self.home_dir = get_proton_home()
        self.connections_file = self.home_dir / "connections.yaml"
        self._connections: Dict[str, ConnectionProfile] = {}
        self._load()

    def _sync_proton_hub_connection(self) -> None:
        """Ensure proton-hub connection profile exists and reflects installed models."""
        from proton.hub.registry import ModelRegistry
        try:
            reg = ModelRegistry()
            installed = reg.list_installed()
        except Exception:
            installed = []

        models_info = [
            ModelInfo(
                id=m.id,
                name=m.name,
                provider="proton-hub",
                connection_id="proton-hub",
                description=f"Local Transformers model: {m.parameters_display} params ({m.size_gb:.1f} GB)",
                capabilities=ModelCapabilities(),
            )
            for m in installed
        ]

        if "proton-hub" not in self._connections and "transformers" in self._connections:
            # Migrate 'transformers' key to 'proton-hub'
            old = self._connections.pop("transformers")
            old.id = "proton-hub"
            old.name = "Proton Model Hub (Local Models)"
            old.provider = ProviderType.PROTON_HUB
            old.status = ConnectionStatus.CONNECTED
            old.discovered_models = models_info
            self._connections["proton-hub"] = old
        elif "proton-hub" not in self._connections:
            self._connections["proton-hub"] = ConnectionProfile(
                id="proton-hub",
                name="Proton Model Hub (Local Models)",
                provider=ProviderType.PROTON_HUB,
                host="127.0.0.1",
                port=0,
                protocol="local",
                base_path="",
                enabled=True,
                status=ConnectionStatus.CONNECTED,
                discovered_models=models_info,
            )
        else:
            conn = self._connections["proton-hub"]
            conn.name = "Proton Model Hub (Local Models)"
            conn.provider = ProviderType.PROTON_HUB
            conn.status = ConnectionStatus.CONNECTED
            conn.discovered_models = models_info

    def _load(self) -> None:
        if self.connections_file.exists():
            try:
                with open(self.connections_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    for cid, cdata in data.items():
                        cdata["id"] = cid
                        self._connections[cid] = ConnectionProfile(**cdata)
            except Exception:
                pass

        # If no connections configured, initialize sensible defaults
        if not self._connections:
            self._init_defaults()
        else:
            self._sync_proton_hub_connection()

    def _init_defaults(self) -> None:
        """Create default profiles for Proton Model Hub, local LM Studio, and Ollama."""
        default_hub = ConnectionProfile(
            id="proton-hub",
            name="Proton Model Hub (Local Models)",
            provider=ProviderType.PROTON_HUB,
            host="127.0.0.1",
            port=0,
            protocol="local",
            base_path="",
            enabled=True,
            status=ConnectionStatus.CONNECTED,
        )
        default_lmstudio = ConnectionProfile(
            id="default-lmstudio",
            name="Local LM Studio",
            provider=ProviderType.LMSTUDIO,
            host="127.0.0.1",
            port=1234,
            protocol="http",
            base_path="/v1",
            enabled=True,
        )
        default_ollama = ConnectionProfile(
            id="default-ollama",
            name="Local Ollama",
            provider=ProviderType.OLLAMA,
            host="127.0.0.1",
            port=11434,
            protocol="http",
            base_path="/v1",
            enabled=True,
        )
        self._connections["proton-hub"] = default_hub
        self._connections["default-lmstudio"] = default_lmstudio
        self._connections["default-ollama"] = default_ollama
        self._sync_proton_hub_connection()
        self.save()

    def save(self) -> None:
        """Persist all connection profiles to disk."""
        data = {cid: conn.model_dump(mode="json", exclude={"id"}) for cid, conn in self._connections.items()}
        with open(self.connections_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def list_connections(self) -> List[ConnectionProfile]:
        self._sync_proton_hub_connection()
        return list(self._connections.values())

    def get_connection(self, connection_id: str) -> Optional[ConnectionProfile]:
        if connection_id == "transformers" and "transformers" not in self._connections:
            connection_id = "proton-hub"
        elif connection_id == "proton-hub" and "proton-hub" not in self._connections:
            connection_id = "transformers"
        return self._connections.get(connection_id)

    def add_connection(self, profile: ConnectionProfile) -> None:
        self._connections[profile.id] = profile
        self.save()

    def remove_connection(self, connection_id: str) -> bool:
        if connection_id in self._connections:
            del self._connections[connection_id]
            self.save()
            return True
        return False

    def get_active_connection(self) -> ConnectionProfile:
        active_id = self.config_mgr.config.active_connection
        if active_id == "transformers":
            active_id = "proton-hub"

        conn = self.get_connection(active_id)
        if conn:
            return conn

        # Fallback to first available
        if self._connections:
            first_id = next(iter(self._connections))
            return self._connections[first_id]
        # Fallback create
        self._init_defaults()
        return self._connections["proton-hub"]

    def set_active_connection(self, connection_id: str) -> bool:
        target_id = connection_id
        if target_id == "transformers" and "transformers" not in self._connections:
            target_id = "proton-hub"
        elif target_id == "proton-hub" and "proton-hub" not in self._connections:
            target_id = "transformers"

        if target_id in self._connections:
            self.config_mgr.set_active_connection(target_id)
            if target_id in ("proton-hub", "transformers"):
                from proton.hub.registry import ModelRegistry
                reg = ModelRegistry()
                def_m = reg.get_default_model()
                if def_m:
                    self.config_mgr.set_active_model(def_m.id)
            return True
        return False

    async def test_connection(self, connection_id: str) -> ConnectionTestResult:
        """Run a probe and update connection status and model cache."""
        profile = self.get_connection(connection_id)
        if not profile:
            return ConnectionTestResult(
                success=False,
                connection_id=connection_id,
                host="unknown",
                port=0,
                base_url="",
                error_message=f"Connection profile '{connection_id}' not found.",
            )

        res = await probe_connection(profile)
        profile.last_tested = datetime.now(timezone.utc)
        if res.success:
            profile.status = ConnectionStatus.CONNECTED
            profile.latency_ms = res.latency_ms
            # Update discovered models
            profile.discovered_models = [
                ModelInfo(
                    id=m_id,
                    name=m_id,
                    provider=profile.provider.value,
                    connection_id=profile.id,
                    capabilities=ModelCapabilities(),
                )
                for m_id in res.discovered_models
            ]
        else:
            profile.status = ConnectionStatus.UNREACHABLE

        self.save()
        return res

    async def refresh_all(self) -> Dict[str, ConnectionTestResult]:
        """Probe all enabled connections and refresh models."""
        results: Dict[str, ConnectionTestResult] = {}
        for cid, profile in self._connections.items():
            if profile.enabled:
                res = await self.test_connection(cid)
                results[cid] = res
        return results

    def get_all_models(self) -> List[ModelInfo]:
        """Aggregate all discovered models across all active connections."""
        models: List[ModelInfo] = []
        for profile in self._connections.values():
            if profile.enabled and profile.discovered_models:
                models.extend(profile.discovered_models)
        return models
