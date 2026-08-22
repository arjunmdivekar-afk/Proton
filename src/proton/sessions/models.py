"""Session data models for persistent conversation storage."""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from proton.core.types import Message, Role


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    model_id: Optional[str] = None
    connection_id: Optional[str] = None


class SessionDetail(BaseModel):
    id: str
    title: str
    workspace_path: str
    connection_id: Optional[str] = None
    model_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: List[Message] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
