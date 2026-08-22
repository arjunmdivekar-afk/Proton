"""Task Execution Engine with real-time checkpointing and telemetry."""

import asyncio
import time
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.tasks.models import ProtonTask, TaskStatus, TaskStep, TaskStepStatus, CommandLog, ToolCallLog, TestLog, ApprovalLog
from proton.tasks.manager import TaskManager
from proton.agent.max_agent import ProtonMaxAgent


class TaskRunner:
    """Executes or resumes persistent tasks with continuous state recording."""

    def __init__(self, manager: Optional[TaskManager] = None) -> None:
        self.manager = manager or TaskManager()
        self.console = Console(safe_box=True)

    async def run_task(self, task_id: str, auto_approve: bool = False) -> Optional[ProtonTask]:
        """Execute or resume a task by ID."""
        task = self.manager.get_task(task_id)
        if not task:
            self.console.print(f"[bold red]Task '{task_id}' not found.[/bold red]")
            return None

        if task.status == TaskStatus.COMPLETED:
            self.console.print(f"[yellow]Task '{task.id}' is already COMPLETED. Use `proton task show {task.id}` to inspect results.[/yellow]")
            return task

        if task.status == TaskStatus.CANCELLED:
            self.console.print(f"[yellow]Task '{task.id}' is CANCELLED. Re-opening task to PENDING state.[/yellow]")
            task.status = TaskStatus.PENDING

        workspace_path = Path(task.workspace_path) if task.workspace_path else Path.cwd()
        if not workspace_path.exists():
            workspace_path = Path.cwd()
            task.workspace_path = str(workspace_path)

        # Transition status to IN_PROGRESS
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.manager.save_task(task)

        self.console.print(
            Panel.fit(
                f"[bold cyan]▶ RUNNING PERSISTENT TASK:[/bold cyan] [bold bright_white]{task.id}[/bold bright_white]\n"
                f"[bold]Goal:[/bold] {task.goal}\n"
                f"[bold]Workspace:[/bold] [dim]{task.workspace_path}[/dim]  "
                f"[bold]Status:[/bold] [yellow]{task.status.value}[/yellow]  "
                f"[bold]Progress:[/bold] [cyan]{task.progress_pct}%[/cyan]",
                border_style="cyan",
            )
        )

        # Initialize MaxAgent on the task workspace
        agent = ProtonMaxAgent(
            workspace_path=workspace_path,
            auto_approve=auto_approve,
            max_steps=30,
        )

        try:
            # Run autonomous agent lifecycle
            report = await agent.run(task.goal)

            # Sync results back to task record
            task.files_changed = list(set(task.files_changed + report.files_modified + report.files_created))
            task.report_file = report.report_path
            task.final_result = report.summary or "Task execution finished."

            # Update plan steps from agent plan if generated
            if agent.plan and agent.plan.steps:
                task.plan = [
                    TaskStep(
                        index=s.index,
                        description=s.description,
                        status=TaskStepStatus.COMPLETED if report.status == "SUCCESS" else TaskStepStatus.PENDING,
                    )
                    for s in agent.plan.steps
                ]

            # Record test run in tests log
            if report.test_output:
                task.tests.append(
                    TestLog(
                        command="automated test suite",
                        passed=report.tests_passed,
                        output=report.test_output[:1000],
                    )
                )

            # Final status transition
            if report.status == "SUCCESS":
                task.status = TaskStatus.COMPLETED
                task.progress_pct = 100
            elif report.status == "CANCELLED_BY_USER":
                task.status = TaskStatus.PAUSED
            else:
                task.status = TaskStatus.COMPLETED if report.tests_passed else TaskStatus.FAILED

            task.update_progress()
            self.manager.save_task(task)

            self.console.print(f"[bold green]✓ Task '{task.id}' saved and updated ({task.status.value}).[/bold green]")
            return task

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.errors.append(f"Execution failure: {e}")
            task.update_progress()
            self.manager.save_task(task)
            self.console.print(f"[bold red]Task '{task.id}' encountered an error: {e}[/bold red]")
            return task
