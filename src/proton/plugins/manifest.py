"""Plugin manifest definition and permission schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginPermission(str):
    pass


class PluginManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    description: str
    author: Optional[str] = None
    entrypoint: str = "plugin.py"
    permissions: List[str] = Field(default_factory=list)
    min_proton_version: str = "0.1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
