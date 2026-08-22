"""Core data types and enums for Proton."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class RiskLevel(str, Enum):
    SAFE = "safe"              # Read-only, inspection
    MODIFICATION = "modification"  # File writes, commits
    EXECUTION = "execution"    # Shell commands, build, test
    DESTRUCTIVE = "destructive"  # Deletions, git push, drop db


class ApprovalDecision(str, Enum):
    ALLOW_ONCE = "allow_once"
    ALLOW_SESSION = "allow_session"
    DENY = "deny"


class ApprovalPolicy(str, Enum):
    STRICT = "strict"          # Level 1: Ask for everything
    BALANCED = "balanced"      # Level 2: Auto safe, ask modification/execution
    AUTONOMOUS = "autonomous"  # Level 4: Auto all within workspace, ask destructive


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    role: Role
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_call_id: str
    name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelCapabilities(BaseModel):
    chat: bool = True
    streaming: bool = True
    tools: bool = True
    vision: bool = False
    embeddings: bool = False
    context_window: int = 128000


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    connection_id: Optional[str] = None
    capabilities: ModelCapabilities = Field(default_factory=ModelCapabilities)
    context_window: int = 128000
    description: Optional[str] = None
