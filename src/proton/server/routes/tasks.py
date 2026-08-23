"""Persistent Task API routes with Python client examples."""

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


@router.post(
    "",
    summary="Create Persistent Task",
    response_model=TaskResponse,
)
async def create_task(req: TaskCreateRequest):
    """
    Create and persist a new development task on disk (`~/.proton/tasks/`).

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/tasks"
    payload = {
        "title": "ESP32 Camera Streaming Server",
        "goal": "Build an ESP32 web server that streams MJPEG video over WiFi on port 80",
        "auto_approve": False,
        "max_steps": 30
    }

    response = requests.post(url, json=payload)
    task = response.json()
    print("Created Task ID:", task["id"])
    print("Status:", task["status"])
    ```
    """
    task = task_mgr.create_task(goal=req.goal, title=req.title)
    return _to_response(task)


@router.get(
    "",
    summary="List All Persistent Tasks",
    response_model=TaskListResponse,
)
async def list_tasks(status: Optional[str] = None):
    """
    List all tracked persistent tasks, optionally filtered by status (`PENDING`, `IN_PROGRESS`, `PAUSED`, `COMPLETED`).

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/tasks"
    params = {"status": "IN_PROGRESS"}

    response = requests.get(url, params=params)
    data = response.json()
    print(f"Total Tasks: {data['total']}")
    for t in data["tasks"]:
        print(f"- [{t['status']}] {t['title']} ({t['progress']}%)")
    ```
    """
    status_filter = TaskStatus(status.upper()) if status else None
    tasks = task_mgr.list_tasks(status=status_filter)
    return TaskListResponse(total=len(tasks), tasks=[_to_response(t) for t in tasks])


@router.get(
    "/{task_id}",
    summary="Get Task Details & Checkpoints",
    response_model=TaskResponse,
)
async def get_task(task_id: str):
    """
    Fetch complete state and execution checkpoints for a specific task.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    task_id = "task-d30dbb25"
    response = requests.get(f"http://127.0.0.1:8787/v1/tasks/{task_id}")
    task = response.json()
    print(f"Title: {task['title']}")
    print(f"Files Modified: {task['files_modified']}")
    print(f"Plan Steps: {task['plan']}")
    ```
    """
    task = task_mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return _to_response(task)


@router.post(
    "/{task_id}/run",
    summary="Execute or Resume Task",
    response_model=TaskResponse,
)
async def run_task(task_id: str, auto_approve: bool = True):
    """
    Execute or resume an active task using the Max-Level Autonomous Agent.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    task_id = "task-d30dbb25"
    response = requests.post(
        f"http://127.0.0.1:8787/v1/tasks/{task_id}/run",
        params={"auto_approve": True}
    )
    task = response.json()
    print("Execution Finished. Status:", task["status"])
    ```
    """
    task = task_mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    updated = await task_runner.run_task(task_id, auto_approve=auto_approve)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to execute task.")
    return _to_response(updated)


@router.post(
    "/{task_id}/pause",
    summary="Pause Task Execution",
    response_model=TaskResponse,
)
async def pause_task(task_id: str):
    """
    Pause an active task and freeze its state checkpoint.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    task_id = "task-d30dbb25"
    response = requests.post(f"http://127.0.0.1:8787/v1/tasks/{task_id}/pause")
    print("Paused:", response.json()["status"])
    ```
    """
    task = task_mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    task.status = TaskStatus.PAUSED
    task_mgr.save_task(task)
    return _to_response(task)


@router.delete(
    "/{task_id}",
    summary="Delete Task Checkpoint",
)
async def delete_task(task_id: str):
    """
    Permanently delete a task JSON checkpoint from disk.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    task_id = "task-d30dbb25"
    response = requests.delete(f"http://127.0.0.1:8787/v1/tasks/{task_id}")
    print("Deleted Status:", response.json())
    ```
    """
    success = task_mgr.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return {"status": "deleted", "id": task_id}
