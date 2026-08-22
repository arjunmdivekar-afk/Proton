"""Persistent Task Manager with JSON checkpoint storage."""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from proton.core.config import get_proton_home
from proton.tasks.models import ProtonTask, TaskStatus, TaskStep, TaskStepStatus


class TaskManager:
    """Manages persistent task lifecycle, storage, and retrieval."""

    def __init__(self, tasks_dir: Optional[Path] = None) -> None:
        self.tasks_dir = tasks_dir or (get_proton_home() / "tasks")
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _get_task_path(self, task_id: str) -> Path:
        clean_id = task_id if task_id.endswith(".json") else f"{task_id}.json"
        return self.tasks_dir / clean_id

    def create_task(
        self,
        goal: str,
        title: Optional[str] = None,
        workspace_path: Optional[Path] = None,
        plan_steps: Optional[List[TaskStep]] = None,
    ) -> ProtonTask:
        """Create and persist a new task in PENDING state."""
        clean_title = title or (goal[:60] + "..." if len(goal) > 60 else goal)
        ws_str = str((workspace_path or Path.cwd()).resolve())

        task = ProtonTask(
            title=clean_title,
            goal=goal,
            status=TaskStatus.PENDING,
            workspace_path=ws_str,
            plan=plan_steps or [],
        )
        task.update_progress()
        self.save_task(task)
        return task

    def save_task(self, task: ProtonTask) -> None:
        """Persist task record to JSON checkpoint."""
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_file = self._get_task_path(task.id)
        with open(task_file, "w", encoding="utf-8") as f:
            f.write(task.model_dump_json(indent=2))

    def get_task(self, task_id: str) -> Optional[ProtonTask]:
        """Fetch task by ID (supports exact ID or prefix match)."""
        # Exact match
        exact_file = self._get_task_path(task_id)
        if exact_file.exists():
            try:
                with open(exact_file, "r", encoding="utf-8") as f:
                    return ProtonTask.model_validate_json(f.read())
            except Exception:
                return None

        # Prefix search match
        search_term = task_id.lower().replace(".json", "")
        for f in self.tasks_dir.glob("*.json"):
            stem = f.stem.lower()
            if stem == search_term or stem.startswith(search_term) or search_term in stem:
                try:
                    with open(f, "r", encoding="utf-8") as rf:
                        return ProtonTask.model_validate_json(rf.read())
                except Exception:
                    continue
        return None

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[ProtonTask]:
        """List all persisted tasks sorted by creation date (newest first)."""
        tasks: List[ProtonTask] = []
        for f in self.tasks_dir.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as rf:
                    t = ProtonTask.model_validate_json(rf.read())
                    if status is None or t.status == status:
                        tasks.append(t)
            except Exception:
                continue

        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    def update_status(self, task_id: str, status: TaskStatus) -> Optional[ProtonTask]:
        """Update task status and persist."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = status
        task.update_progress()
        self.save_task(task)
        return task

    def pause_task(self, task_id: str) -> Optional[ProtonTask]:
        return self.update_status(task_id, TaskStatus.PAUSED)

    def cancel_task(self, task_id: str) -> Optional[ProtonTask]:
        return self.update_status(task_id, TaskStatus.CANCELLED)

    def delete_task(self, task_id: str) -> bool:
        """Delete task checkpoint from disk."""
        task = self.get_task(task_id)
        if not task:
            return False
        task_file = self._get_task_path(task.id)
        if task_file.exists():
            task_file.unlink()
            return True
        return False
