"""Connection schema definitions for Proton."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from proton.core.types import ModelInfo


class ProviderType(str, Enum):
    TRANSFORMERS = "transformers"
    LMSTUDIO = "lmstudio"
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"
    OPENAI = "openai"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    AUTH_REQUIRED = "auth_required"
    MISCONFIGURED = "misconfigured"
    DISABLED = "disabled"


class ConnectionProfile(BaseModel):
    id: str
    name: str
    provider: ProviderType = ProviderType.LMSTUDIO
    host: str = "127.0.0.1"
    port: int = 1234
    protocol: str = "http"
    base_path: str = "/v1"
    api_key: Optional[str] = None
    enabled: bool = True
    timeout_seconds: float = 180.0
    status: ConnectionStatus = ConnectionStatus.UNREACHABLE
    last_tested: Optional[datetime] = None
    latency_ms: Optional[float] = None
    discovered_models: List[ModelInfo] = Field(default_factory=list)
    custom_headers: dict = Field(default_factory=dict)

    @property
    def base_url(self) -> str:
        """Construct full base URL, e.g. http://192.168.1.50:1234/v1"""
        # Normalize base_path
        path = self.base_path.strip("/")
        base = f"{self.protocol}://{self.host}:{self.port}"
        return f"{base}/{path}" if path else base

    @property
    def is_local(self) -> bool:
        return self.host in ("127.0.0.1", "localhost", "0.0.0.0", "::1")


class ConnectionTestResult(BaseModel):
    success: bool
    connection_id: str
    host: str
    port: int
    base_url: str
    tcp_reachable: bool = False
    http_reachable: bool = False
    models_endpoint_reachable: bool = False
    latency_ms: Optional[float] = None
    discovered_models: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    remediation_advice: Optional[str] = None
