"""Pydantic data models for Proton Persistent Task Management."""

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TaskStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStep(BaseModel):
    index: int
    description: str
    status: TaskStepStatus = TaskStepStatus.PENDING
    tool_name: Optional[str] = None
    output: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class CommandLog(BaseModel):
    command: str
    exit_code: int = 0
    stdout_preview: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ToolCallLog(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class TestLog(BaseModel):
    command: str
    passed: bool
    output: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ApprovalLog(BaseModel):
    tool_name: str
    action: str
    decision: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ProtonTask(BaseModel):
    id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    title: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    progress_pct: int = 0
    workspace_path: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Checkpoints & execution state
    plan: List[TaskStep] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    commands_executed: List[CommandLog] = Field(default_factory=list)
    tool_calls: List[ToolCallLog] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    approvals: List[ApprovalLog] = Field(default_factory=list)
    tests: List[TestLog] = Field(default_factory=list)
    final_result: Optional[str] = None
    report_file: Optional[str] = None

    def update_progress(self) -> None:
        """Calculate progress percentage based on completed plan steps."""
        if not self.plan:
            self.progress_pct = 100 if self.status == TaskStatus.COMPLETED else 0
            return
        completed = sum(1 for s in self.plan if s.status == TaskStepStatus.COMPLETED)
        self.progress_pct = int((completed / len(self.plan)) * 100)
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
