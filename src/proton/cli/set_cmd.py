"""CLI commands for configuring Proton model execution hardware device mode (CPU / GPU / Partial)."""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.core.config import ConfigManager
from proton.hub.hardware import detect_hardware

set_app = typer.Typer(
    help="Configure model hardware execution device mode (CPU, GPU, Partial).",
    invoke_without_command=True,
)
console = Console()


def _render_device_status_panel(active_mode: str) -> None:
    """Render a visual hardware and device execution status panel."""
    hw = detect_hardware()

    mode_display = {
        "cpu": "[bold cyan]CPU & System RAM[/bold cyan] (Zero GPU utilization)",
        "gpu": "[bold green]GPU Dedicated[/bold green] (NVIDIA CUDA / Apple MPS)",
        "partial": "[bold magenta]PARTIAL Hybrid[/bold magenta] (CPU + GPU Layer Offloading)",
        "auto": "[bold yellow]AUTO Detection[/bold yellow] (Auto-selects optimal hardware)",
    }.get(active_mode.lower(), f"[bold white]{active_mode.upper()}[/bold white]")

    table = Table(box=None, padding=(0, 2), show_header=False)
    table.add_column("Property", style="bold white", width=24)
    table.add_column("Value", style="cyan")

    table.add_row("Active Execution Mode", mode_display)
    table.add_row("Host CPU", f"{hw.cpu_count_physical} Cores ({hw.cpu_arch})")
    table.add_row("System RAM", f"{hw.available_ram_gb:.2f} GB Available / {hw.total_ram_gb:.2f} GB Total")
    if hw.has_cuda:
        table.add_row("NVIDIA GPU", f"{hw.cuda_device_name or 'CUDA'} ({hw.cuda_vram_gb:.2f} GB VRAM)")
    elif hw.has_mps:
        table.add_row("Apple GPU", "Apple Silicon Unified Memory (MPS)")
    else:
        table.add_row("GPU Detected", "[dim]None (CPU-only system)[/dim]")

    panel = Panel(
        table,
        title="[bold cyan]⚛️ PROTON HARDWARE INFERENCE CONFIGURATION[/bold cyan]",
        subtitle="[dim]Use `proton set --CPU`, `proton set --GPU`, or `proton set --Partial` to switch[/dim]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def set_hardware_mode(mode: str) -> None:
    """Core logic to set hardware execution mode and persist to config."""
    mode_clean = mode.lower().strip()
    if mode_clean not in ("cpu", "gpu", "partial", "auto"):
        console.print(f"[bold red]✗ Invalid mode '{mode}'.[/bold red] Valid options: `cpu`, `gpu`, `partial`, `auto`.")
        raise typer.Exit(1)

    config_mgr = ConfigManager()
    config_mgr.set_device_mode(mode_clean)

    hw = detect_hardware()

    if mode_clean == "cpu":
        console.print(
            Panel(
                "[bold green]✓ Hardware Execution Mode set to CPU & RAM.[/bold green]\n\n"
                "[cyan]• Model runtime:[/cyan] Strict CPU execution + System RAM\n"
                "[cyan]• GPU utilization:[/cyan] 0% (No GPU memory allocated)\n"
                "[cyan]• Ideal for:[/cyan] Machines without dedicated GPU or conserving VRAM\n"
                f"[dim]• Available System RAM: {hw.available_ram_gb:.2f} GB / {hw.total_ram_gb:.2f} GB[/dim]",
                title="[bold green]⚡ Proton Hardware Set: CPU[/bold green]",
                border_style="green",
            )
        )
    elif mode_clean == "gpu":
        gpu_info = f"{hw.cuda_device_name} ({hw.cuda_vram_gb:.2f} GB VRAM)" if hw.has_cuda else (
            "Apple Silicon MPS" if hw.has_mps else "[yellow]Warning: No physical GPU detected, will fallback to CPU[/yellow]"
        )
        console.print(
            Panel(
                "[bold green]✓ Hardware Execution Mode set to GPU Dedicated.[/bold green]\n\n"
                "[cyan]• Model runtime:[/cyan] Maximum GPU tensor acceleration (CUDA / MPS)\n"
                "[cyan]• CPU utilization:[/cyan] 0% inference computation\n"
                "[cyan]• Ideal for:[/cyan] Fast low-latency generation & dedicated GPU workloads\n"
                f"[dim]• Detected GPU: {gpu_info}[/dim]",
                title="[bold green]⚡ Proton Hardware Set: GPU[/bold green]",
                border_style="green",
            )
        )
    elif mode_clean == "partial":
        console.print(
            Panel(
                "[bold green]✓ Hardware Execution Mode set to PARTIAL (Hybrid Mixture).[/bold green]\n\n"
                "[cyan]• Model runtime:[/cyan] Balanced mixture of GPU VRAM + CPU System RAM\n"
                "[cyan]• Layer splitting:[/cyan] Automatically offloads layers to CPU when VRAM fills\n"
                "[cyan]• Ideal for:[/cyan] Running larger models (7B, 14B) on modest 4GB–8GB GPUs\n"
                f"[dim]• Available: {hw.available_ram_gb:.2f} GB RAM + {hw.cuda_vram_gb:.2f} GB VRAM[/dim]",
                title="[bold green]⚡ Proton Hardware Set: PARTIAL[/bold green]",
                border_style="magenta",
            )
        )
    else:
        console.print(f"[bold green]✓ Hardware Execution Mode reset to AUTO.[/bold green]")


@set_app.callback(invoke_without_command=True)
def set_main(
    ctx: typer.Context,
    mode: Optional[str] = typer.Argument(None, help="Hardware mode: cpu, gpu, partial, auto"),
    cpu: bool = typer.Option(False, "--cpu", "--CPU", help="Set model execution to CPU and System RAM (No GPU)"),
    gpu: bool = typer.Option(False, "--gpu", "--GPU", help="Set model execution to GPU dedicated (No CPU)"),
    partial: bool = typer.Option(False, "--partial", "--Partial", help="Set model execution to Partial (CPU + GPU mixture)"),
    auto: bool = typer.Option(False, "--auto", "--Auto", help="Auto-detect optimal device execution mode"),
):
    """
    Set model execution hardware device mode across all installed models.

    Examples:
      proton set --CPU
      proton set --GPU
      proton set --Partial
      proton set
    """
    if ctx.invoked_subcommand is not None:
        return

    # Check flags
    if cpu:
        set_hardware_mode("cpu")
    elif gpu:
        set_hardware_mode("gpu")
    elif partial:
        set_hardware_mode("partial")
    elif auto:
        set_hardware_mode("auto")
    elif mode:
        set_hardware_mode(mode)
    else:
        config_mgr = ConfigManager()
        active_mode = config_mgr.config.device_mode or "auto"
        _render_device_status_panel(active_mode)
