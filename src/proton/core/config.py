"""Configuration management system for Proton."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

from proton.core.types import ApprovalPolicy


class SecurityConfig(BaseModel):
    approval_policy: ApprovalPolicy = ApprovalPolicy.STRICT
    sandbox_workspace_only: bool = True
    allowed_commands: List[str] = Field(
        default_factory=lambda: [
            "git", "python", "pytest", "npm", "node", "pip", "cargo", "go", "ls", "dir", "cat", "find"
        ]
    )
    blocked_commands: List[str] = Field(
        default_factory=lambda: [
            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "format c:", "drop database"
        ]
    )
    redact_secrets: bool = True


class AgentConfig(BaseModel):
    max_steps: int = 30
    max_tool_calls_per_turn: int = 10
    timeout_seconds: int = 180
    autonomy_level: int = 1  # 1 = strict human approval, 2 = balanced


class RAGConfig(BaseModel):
    enabled: bool = True
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k: int = 5
    min_similarity: float = 0.2
    hybrid_search: bool = True
    db_path: Optional[str] = None


class UIConfig(BaseModel):
    theme: str = "default"
    streaming: bool = True
    show_token_counter: bool = True
    show_latency: bool = True


class ProtonConfig(BaseModel):
    active_connection: str = "default-lmstudio"
    active_model: Optional[str] = None
    workspace_dir: str = Field(default_factory=lambda: str(Path.cwd()))
    home_dir: str = Field(default_factory=lambda: str(Path.home() / ".proton"))
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    ui: UIConfig = Field(default_factory=UIConfig)


def get_proton_home() -> Path:
    """Return the base Proton data directory (~/.proton or $PROTON_HOME)."""
    env_home = os.getenv("PROTON_HOME")
    if env_home:
        p = Path(env_home).expanduser().resolve()
    else:
        p = Path.home() / ".proton"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_project_proton_dir() -> Optional[Path]:
    """Return local .proton dir if present in current working directory."""
    cwd = Path.cwd()
    project_dir = cwd / ".proton"
    return project_dir if project_dir.exists() else None


class ConfigManager:
    """Manages loading, merging, saving, and overriding Proton configurations."""

    def __init__(self, workspace_path: Optional[Path] = None) -> None:
        self.workspace_path = workspace_path or Path.cwd()
        self.home_dir = get_proton_home()
        self.global_config_path = self.home_dir / "config.yaml"
        self.project_config_path = self.workspace_path / ".proton" / "config.yaml"
        self._config: ProtonConfig = self._load()

    @property
    def config(self) -> ProtonConfig:
        return self._config

    def _load(self) -> ProtonConfig:
        data: Dict[str, Any] = {}

        # 1. Load global config
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path, "r", encoding="utf-8") as f:
                    global_data = yaml.safe_load(f) or {}
                    data.update(global_data)
            except Exception:
                pass

        # 2. Merge project config
        if self.project_config_path.exists():
            try:
                with open(self.project_config_path, "r", encoding="utf-8") as f:
                    project_data = yaml.safe_load(f) or {}
                    data.update(project_data)
            except Exception:
                pass

        # 3. Environment variable overrides
        if "PROTON_ACTIVE_CONNECTION" in os.environ:
            data["active_connection"] = os.environ["PROTON_ACTIVE_CONNECTION"]
        if "PROTON_ACTIVE_MODEL" in os.environ:
            data["active_model"] = os.environ["PROTON_ACTIVE_MODEL"]

        config = ProtonConfig(**data) if data else ProtonConfig()
        config.workspace_dir = str(self.workspace_path)
        config.home_dir = str(self.home_dir)
        return config

    def save_global(self) -> None:
        """Save current configuration to global ~/.proton/config.yaml."""
        self.home_dir.mkdir(parents=True, exist_ok=True)
        dump_data = self._config.model_dump(mode="json", exclude={"workspace_dir", "home_dir"})
        with open(self.global_config_path, "w", encoding="utf-8") as f:
            yaml.dump(dump_data, f, default_flow_style=False, sort_keys=False)

    def set_active_connection(self, connection_id: str) -> None:
        self._config.active_connection = connection_id
        self.save_global()

    def set_active_model(self, model_id: Optional[str]) -> None:
        self._config.active_model = model_id
        self.save_global()

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if hasattr(self._config, k):
                setattr(self._config, k, v)
        self.save_global()
