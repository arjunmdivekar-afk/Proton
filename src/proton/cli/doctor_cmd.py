"""Doctor diagnostics for Proton environment and provider health."""

import asyncio
import os
import sys
import shutil
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.core.config import get_proton_home, ConfigManager
from proton.connection.manager import ConnectionManager


async def run_doctor_checks(workspace_path: Optional[Path] = None) -> None:
    console = Console()
    workspace = (workspace_path or Path.cwd()).resolve()

    console.print(Panel.fit("[bold cyan]PROTON SYSTEM & CONNECTION DIAGNOSTICS[/bold cyan]", border_style="cyan"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="bold")
    table.add_column("Check")
    table.add_column("Status", width=12)
    table.add_column("Details")

    # 1. Python Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_status = "[green]✓ OK[/green]" if sys.version_info >= (3, 10) else "[red]✗ Outdated[/red]"
    table.add_row("Runtime", "Python Version", py_status, f"Python {py_ver} ({sys.executable})")

    # 2. Filesystem & Proton Home
    home = get_proton_home()
    home_ok = home.exists() and os.access(home, os.W_OK)
    home_status = "[green]✓ OK[/green]" if home_ok else "[red]✗ Permission[/red]"
    table.add_row("Filesystem", "Proton Home Dir", home_status, str(home))

    ws_ok = workspace.exists() and os.access(workspace, os.W_OK)
    ws_status = "[green]✓ OK[/green]" if ws_ok else "[red]✗ Permission[/red]"
    table.add_row("Filesystem", "Workspace", ws_status, str(workspace))

    # 3. Git Tooling
    git_path = shutil.which("git")
    git_status = "[green]✓ Found[/green]" if git_path else "[yellow]○ Missing[/yellow]"
    table.add_row("Tooling", "Git Executable", git_status, git_path or "Git not found on PATH")

    # 4. SQLite Storage
    db_file = home / "proton.db"
    db_status = "[green]✓ Ready[/green]" if db_file.exists() else "[dim]Initialized on run[/dim]"
    table.add_row("Storage", "SQLite DB", db_status, str(db_file))

    # 5. Model Connection Health
    config_mgr = ConfigManager(workspace)
    conn_mgr = ConnectionManager(config_mgr)
    active_conn = conn_mgr.get_active_connection()

    table.add_row(
        "AI Connection",
        f"Active Provider ({active_conn.provider.value})",
        "[yellow]Probing...[/yellow]",
        active_conn.base_url,
    )

    console.print(table)
    console.print(f"\n[cyan]Probing active endpoint: {active_conn.base_url}...[/cyan]")

    test_res = await conn_mgr.test_connection(active_conn.id)
    if test_res.success:
        console.print(f"[bold green]✓ AI Endpoint is Healthy![/bold green] (Latency: {test_res.latency_ms:.1f}ms)")
        if test_res.discovered_models:
            console.print(f"[green]Discovered Models on {active_conn.name}:[/green]")
            for m in test_res.discovered_models:
                console.print(f"  • [cyan]{m}[/cyan]")
    else:
        console.print(f"[bold red]✗ AI Endpoint unreachable:[/bold red] {test_res.error_message}")
        if test_res.remediation_advice:
            console.print(f"\n[bold yellow]Remediation:[/bold yellow]\n{test_res.remediation_advice}")
        console.print("\n[dim]Tip: Use `proton connection` to change the IP address and port.[/dim]")
