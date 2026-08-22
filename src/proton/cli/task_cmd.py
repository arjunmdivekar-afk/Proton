"""CLI subcommands for Proton Persistent Task Management (`proton task`)."""

import asyncio
from typing import Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from proton.tasks.models import TaskStatus, TaskStepStatus
from proton.tasks.manager import TaskManager
from proton.tasks.runner import TaskRunner

task_app = typer.Typer(
    help="Manage persistent development tasks (create, list, show, run, pause, resume, cancel).",
    no_args_is_help=True,
)
console = Console(safe_box=True)


@task_app.command("create")
def create_task_cmd(
    title: str = typer.Argument(..., help="Short title for the task (e.g. 'simple AI UI' or 'ESP32 Camera Server')"),
    goal: Optional[str] = typer.Argument(None, help="Detailed goal/objective (e.g. 'Create a simple web UI for an AI assistant'). If omitted, title is used as goal."),
) -> None:
    """Create a new persistent task with title and goal: `proton task create \"<title>\" \"<goal>\"`."""
    actual_goal = goal.strip() if (goal and goal.strip()) else title.strip()
    manager = TaskManager()
    task = manager.create_task(goal=actual_goal, title=title.strip(), workspace_path=Path.cwd())

    console.print(
        Panel.fit(
            f"[bold green]✓ Created Persistent Task:[/bold green] [bold cyan]{task.id}[/bold cyan]\n\n"
            f"[bold]Title:[/bold] {task.title}\n"
            f"[bold]Goal:[/bold] {task.goal}\n"
            f"[bold]Status:[/bold] [yellow]{task.status.value}[/yellow]  "
            f"[bold]Workspace:[/bold] [dim]{task.workspace_path}[/dim]\n\n"
            f"[dim]Run this task anytime with:[/dim] [bold bright_white]proton task run {task.id}[/bold bright_white]",
            border_style="green",
        )
    )


@task_app.command("list")
def list_tasks_cmd(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter tasks by status (PENDING, IN_PROGRESS, PAUSED, COMPLETED, CANCELLED)"),
) -> None:
    """List all persistent development tasks with status and progress."""
    manager = TaskManager()
    status_filter = TaskStatus(status.upper()) if status else None
    tasks = manager.list_tasks(status=status_filter)

    if not tasks:
        console.print("[yellow]No persistent tasks found.[/yellow]")
        console.print("[dim]Create your first task with:[/dim] `proton task create \"<goal>\"`")
        return

    table = Table(title="Proton Persistent Tasks", show_header=True, header_style="bold cyan")
    table.add_column("Task ID", style="bold cyan", width=14)
    table.add_column("Status", width=14)
    table.add_column("Progress", width=10)
    table.add_column("Title", style="bold")
    table.add_column("Created", style="dim", width=19)

    for t in tasks:
        status_style = {
            TaskStatus.PENDING: "[dim yellow]● PENDING[/dim yellow]",
            TaskStatus.IN_PROGRESS: "[bold cyan]▶ IN_PROGRESS[/bold cyan]",
            TaskStatus.PAUSED: "[yellow]⏸ PAUSED[/yellow]",
            TaskStatus.COMPLETED: "[bold green]✓ COMPLETED[/bold green]",
            TaskStatus.CANCELLED: "[dim red]✗ CANCELLED[/dim red]",
            TaskStatus.FAILED: "[bold red]✗ FAILED[/bold red]",
        }.get(t.status, t.status.value)

        prog_bar = f"[{'#' * (t.progress_pct // 10):<10}] {t.progress_pct}%"
        table.add_row(t.id, status_style, prog_bar, t.title, t.created_at)

    console.print(table)


@task_app.command("show")
def show_task_cmd(
    task_id: str = typer.Argument(..., help="Task ID to inspect"),
) -> None:
    """Show detailed record of a task including Goal, Plan, Files Changed, Commands, Tool Calls, and Tests."""
    manager = TaskManager()
    task = manager.get_task(task_id)

    if not task:
        console.print(f"[bold red]Task '{task_id}' not found.[/bold red]")
        return

    status_color = {
        TaskStatus.COMPLETED: "green",
        TaskStatus.IN_PROGRESS: "cyan",
        TaskStatus.PAUSED: "yellow",
        TaskStatus.FAILED: "red",
        TaskStatus.CANCELLED: "dim",
    }.get(task.status, "yellow")

    console.print(
        Panel.fit(
            f"[bold cyan]TASK RECORD: {task.id}[/bold cyan]  [{status_color}]{task.status.value}[/{status_color}]\n"
            f"[bold]Title:[/bold] {task.title}\n"
            f"[bold]Goal:[/bold] {task.goal}\n"
            f"[bold]Workspace:[/bold] [dim]{task.workspace_path}[/dim]\n"
            f"[bold]Progress:[/bold] {task.progress_pct}%  "
            f"[bold]Created:[/bold] [dim]{task.created_at}[/dim]  "
            f"[bold]Updated:[/bold] [dim]{task.updated_at}[/dim]",
            border_style="cyan",
        )
    )

    # 1. Plan & Milestones
    if task.plan:
        console.print("\n[bold cyan]📋 Plan & Milestones:[/bold cyan]")
        for s in task.plan:
            icon = "✓" if s.status == TaskStepStatus.COMPLETED else ("▶" if s.status == TaskStepStatus.RUNNING else "○")
            console.print(f"  {icon} [bold]Step {s.index}:[/bold] {s.description} [dim]({s.status.value})[/dim]")
    else:
        console.print("\n[dim]📋 Plan: Not generated yet (will be formulated upon execution).[/dim]")

    # 2. Files Changed
    if task.files_changed:
        console.print("\n[bold green]📁 Files Modified & Created:[/bold green]")
        for f in task.files_changed:
            console.print(f"  • [cyan]{f}[/cyan]")
    else:
        console.print("\n[dim]📁 Files Changed: None recorded yet.[/dim]")

    # 3. Tests Log
    if task.tests:
        console.print("\n[bold yellow]🧪 Automated Tests Log:[/bold yellow]")
        for t in task.tests:
            icon = "[green]✓ PASSED[/green]" if t.passed else "[red]✗ FAILED[/red]"
            console.print(f"  • {icon} [dim]{t.timestamp}[/dim] — Command: `{t.command}`")

    # 4. Commands Run
    if task.commands_executed:
        console.print("\n[bold magenta]💻 Commands Executed:[/bold magenta]")
        for c in task.commands_executed[-5:]:
            console.print(f"  • [dim]{c.timestamp}[/dim] `{c.command}` (exit {c.exit_code})")

    # 5. Errors
    if task.errors:
        console.print("\n[bold red]⚠️ Errors & Issues:[/bold red]")
        for err in task.errors[-3:]:
            console.print(f"  • [red]{err}[/red]")

    # 6. Final Result / Report
    if task.report_file:
        console.print(f"\n[bold]📄 Execution Audit Report:[/bold] [cyan]{task.report_file}[/cyan]")


@task_app.command("run")
def run_task_cmd(
    task_id: str = typer.Argument(..., help="Task ID to run or continue"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-y", help="Auto-approve plan and tool actions"),
) -> None:
    """Execute or continue a persistent task."""
    runner = TaskRunner()
    asyncio.run(runner.run_task(task_id, auto_approve=auto_approve))


@task_app.command("pause")
def pause_task_cmd(
    task_id: str = typer.Argument(..., help="Task ID to pause"),
) -> None:
    """Pause an active task and freeze its checkpoint."""
    manager = TaskManager()
    task = manager.pause_task(task_id)
    if task:
        console.print(f"[bold yellow]⏸ Task '{task.id}' paused.[/bold yellow] Use `proton task resume {task.id}` to continue.")
    else:
        console.print(f"[bold red]Task '{task_id}' not found.[/bold red]")


@task_app.command("resume")
def resume_task_cmd(
    task_id: str = typer.Argument(..., help="Task ID to resume"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-y", help="Auto-approve plan and tool actions"),
) -> None:
    """Resume and execute a paused or pending task."""
    runner = TaskRunner()
    asyncio.run(runner.run_task(task_id, auto_approve=auto_approve))


@task_app.command("cancel")
def cancel_task_cmd(
    task_id: str = typer.Argument(..., help="Task ID to cancel"),
) -> None:
    """Cancel a task."""
    manager = TaskManager()
    task = manager.cancel_task(task_id)
    if task:
        console.print(f"[bold red]✗ Task '{task.id}' cancelled.[/bold red]")
    else:
        console.print(f"[bold red]Task '{task_id}' not found.[/bold red]")


@task_app.command("delete")
def delete_task_cmd(
    task_id: str = typer.Argument(..., help="Task ID to delete"),
) -> None:
    """Delete a task record and checkpoint."""
    manager = TaskManager()
    success = manager.delete_task(task_id)
    if success:
        console.print(f"[bold green]✓ Deleted task '{task_id}'.[/bold green]")
    else:
        console.print(f"[bold red]Task '{task_id}' not found.[/bold red]")
