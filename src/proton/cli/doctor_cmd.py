"""Doctor diagnostics for Proton environment, provider health, and host system hardware."""

import asyncio
import ctypes
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.core.config import get_proton_home, ConfigManager
from proton.connection.manager import ConnectionManager


class WindowsMemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _get_memory_info() -> Dict[str, str]:
    """Retrieve host RAM statistics."""
    if sys.platform == "win32":
        try:
            stat = WindowsMemoryStatus()
            stat.dwLength = ctypes.sizeof(WindowsMemoryStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

            total_gb = stat.ullTotalPhys / (1024**3)
            avail_gb = stat.ullAvailPhys / (1024**3)
            used_gb = total_gb - avail_gb
            load_pct = stat.dwMemoryLoad

            # Progress bar
            bar_width = 10
            filled = int(round((load_pct / 100.0) * bar_width))
            filled = max(0, min(bar_width, filled))
            unfilled = bar_width - filled
            color = "green" if load_pct < 60 else ("yellow" if load_pct < 85 else "bold red")
            bar = f"[{color}]{'#' * filled}[/{color}][dim]{'-' * unfilled}[/dim]"

            return {
                "total": f"{total_gb:.1f} GB",
                "used": f"{used_gb:.1f} GB",
                "free": f"{avail_gb:.1f} GB",
                "load": f"{load_pct}%",
                "bar": bar,
                "color": color,
            }
        except Exception:
            pass

    return {
        "total": "Unknown",
        "used": "Unknown",
        "free": "Unknown",
        "load": "0%",
        "bar": "[dim]----------[/dim]",
        "color": "dim",
    }


def _get_system_uptime() -> str:
    """Retrieve system uptime."""
    if sys.platform == "win32":
        try:
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            uptime_sec = uptime_ms // 1000
            days = uptime_sec // 86400
            hours = (uptime_sec % 86400) // 3600
            mins = (uptime_sec % 3600) // 60
            secs = uptime_sec % 60
            return f"{days}d {hours}h {mins}m {secs}s"
        except Exception:
            pass
    return "Unknown"


def _get_gpu_info() -> List[Dict[str, str]]:
    """Discover connected GPU and display adapters."""
    gpus: List[Dict[str, str]] = []
    if sys.platform == "win32":
        try:
            cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -Property Name, AdapterRAM, DriverVersion"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
            lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
            if len(lines) >= 3:
                for line in lines[2:]:
                    parts = re_split_whitespace(line)
                    if parts:
                        name = parts[0]
                        gpus.append({"name": name})
        except Exception:
            pass
    return gpus


def re_split_whitespace(text: str) -> List[str]:
    import re
    return re.findall(r"\S+", text)


async def run_system_diagnostics() -> None:
    """Execute host machine hardware and OS diagnostic check."""
    console = Console(safe_box=True)

    console.print(Panel.fit("[bold cyan]PROTON HOST MACHINE & SYSTEM DIAGNOSTICS[/bold cyan]", border_style="cyan"))

    # 1. Host & OS Info Table
    os_table = Table(title="Operating System & Platform", show_header=True, header_style="bold cyan")
    os_table.add_column("Property", style="bold")
    os_table.add_column("Value")

    now = datetime.now().astimezone()
    os_table.add_row("Operating System", f"{platform.system()} {platform.release()} (Build {platform.version()})")
    os_table.add_row("System Architecture", f"{platform.machine()} ({platform.architecture()[0]})")
    os_table.add_row("Computer Hostname", socket.gethostname())
    os_table.add_row("Current User", os.getenv("USERNAME") or os.getenv("USER") or "Unknown")
    os_table.add_row("System Uptime", _get_system_uptime())
    os_table.add_row("Local Date & Time", now.strftime("%A, %B %d, %Y - %I:%M:%S %p %Z"))

    console.print(os_table)
    console.print()

    # 2. CPU & Memory Hardware Table
    hw_table = Table(title="CPU & Memory Hardware", show_header=True, header_style="bold cyan")
    hw_table.add_column("Component", style="bold")
    hw_table.add_column("Specification")
    hw_table.add_column("Usage / Status")

    # CPU
    cpu_cores = os.cpu_count() or 1
    cpu_name = platform.processor() or "Multi-Core Processor"
    hw_table.add_row("Processor (CPU)", f"{cpu_name} ({cpu_cores} Logical Cores)", f"[green]{cpu_cores} Cores Online[/green]")

    # RAM
    mem = _get_memory_info()
    hw_table.add_row(
        "Memory (RAM)",
        f"{mem['used']} Used / {mem['total']} Total (Free: {mem['free']})",
        f"[{mem['bar']}] [{mem['color']}]{mem['load']}[/{mem['color']}]",
    )

    console.print(hw_table)
    console.print()

    # 3. Storage Drives Table
    disk_table = Table(title="Storage Volumes & Partitions", show_header=True, header_style="bold cyan")
    disk_table.add_column("Drive", style="bold cyan", width=8)
    disk_table.add_column("Total Space")
    disk_table.add_column("Used Space")
    disk_table.add_column("Free Space")
    disk_table.add_column("Usage")

    # Check common drives on Windows or root on Linux
    drives_to_check = ["C:\\", "D:\\", "E:\\"] if sys.platform == "win32" else ["/"]
    for drive in drives_to_check:
        if os.path.exists(drive):
            try:
                total, used, free = shutil.disk_usage(drive)
                total_gb = total / (1024**3)
                used_gb = used / (1024**3)
                free_gb = free / (1024**3)
                pct = (used / total) * 100

                bar_width = 10
                filled = int(round((pct / 100.0) * bar_width))
                filled = max(0, min(bar_width, filled))
                unfilled = bar_width - filled
                dcolor = "green" if pct < 75 else ("yellow" if pct < 90 else "bold red")
                dbar = f"[{dcolor}]{'#' * filled}[/{dcolor}][dim]{'-' * unfilled}[/dim]"

                disk_table.add_row(
                    drive,
                    f"{total_gb:.1f} GB",
                    f"{used_gb:.1f} GB",
                    f"{free_gb:.1f} GB",
                    f"[{dbar}] [{dcolor}]{pct:.1f}%[/{dcolor}]",
                )
            except Exception:
                pass

    console.print(disk_table)
    console.print()

    # 4. Network & Connectivity Table
    net_table = Table(title="Network & Host Connectivity", show_header=True, header_style="bold cyan")
    net_table.add_column("Interface", style="bold")
    net_table.add_column("Address / Status")

    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        host_ip = "127.0.0.1"

    net_table.add_row("Primary Local IP", host_ip)
    net_table.add_row("Loopback", "127.0.0.1 (localhost)")

    console.print(net_table)
    console.print()


async def run_doctor_checks(workspace_path: Optional[Path] = None) -> None:
    """Execute Proton application environment, filesystem, and model diagnostics."""
    console = Console(safe_box=True)
    workspace = (workspace_path or Path.cwd()).resolve()

    console.print(Panel.fit("[bold cyan]PROTON APPLICATION & CONNECTION DIAGNOSTICS[/bold cyan]", border_style="cyan"))

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
