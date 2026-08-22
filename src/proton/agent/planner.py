"""Step-by-step task planner and progress tracker."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    index: int
    description: str
    status: StepStatus = StepStatus.PENDING
    tool_name: Optional[str] = None
    result_summary: Optional[str] = None


class Plan(BaseModel):
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)

    def render_markdown(self) -> str:
        lines = [f"**Plan:** {self.goal}\n"]
        for step in self.steps:
            if step.status == StepStatus.COMPLETED:
                icon = "✓"
            elif step.status == StepStatus.RUNNING:
                icon = "●"
            elif step.status == StepStatus.FAILED:
                icon = "✗"
            else:
                icon = "○"
            lines.append(f"{icon} {step.index}. {step.description}")
        return "\n".join(lines)
