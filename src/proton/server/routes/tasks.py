"""Persistent Task API routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks

from proton.server.schemas import TaskCreateRequest, TaskResponse, TaskListResponse
from proton.tasks.manager import TaskManager
from proton.tasks.runner import TaskRunner
from proton.tasks.models import TaskStatus

router = APIRouter(prefix="/v1/tasks", tags=["Tasks"])
task_mgr = TaskManager()
task_runner = TaskRunner(task_mgr)


def _to_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        goal=task.goal,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
        progress=task.progress_pct,
        plan=[s.description if hasattr(s, "description") else str(s) for s in task.plan],
        files_modified=task.files_changed,
        commands_executed=[c.command if hasattr(c, "command") else str(c) for c in task.commands_executed],
        errors=task.errors,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("", response_model=TaskResponse)
async def create_task(req: TaskCreateRequest):
    """Create a new persistent engineering task."""
    task = task_mgr.create_task(goal=req.goal, title=req.title)
    return _to_response(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(status: Optional[str] = None):
    """List all tracked persistent tasks."""
    status_filter = TaskStatus(status.upper()) if status else None
    tasks = task_mgr.list_tasks(status=status_filter)
    return TaskListResponse(total=len(tasks), tasks=[_to_response(t) for t in tasks])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get full state and checkpoints of a specific task."""
    task = task_mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return _to_response(task)


@router.post("/{task_id}/run", response_model=TaskResponse)
async def run_task(task_id: str, background_tasks: BackgroundTasks, auto_approve: bool = True):
    """Execute or resume a persistent task."""
    task = task_mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    # Execute in background or synchronously
    updated = await task_runner.run_task(task_id, auto_approve=auto_approve)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to execute task.")
    return _to_response(updated)


@router.post("/{task_id}/pause", response_model=TaskResponse)
async def pause_task(task_id: str):
    """Pause an active task and freeze state."""
    task = task_mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    task.status = TaskStatus.PAUSED
    task_mgr.save_task(task)
    return _to_response(task)


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task checkpoint."""
    success = task_mgr.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {"status": "deleted", "id": task_id}
