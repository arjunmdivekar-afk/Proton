"""CLI commands for Proton Model Hub (`proton model-hub`)."""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.hub.tui import ModelHubTUI
from proton.hub.client import HuggingFaceHubClient
from proton.hub.registry import ModelRegistry
from proton.hub.hardware import detect_hardware, assess_model_fit
from proton.hub.downloader import ModelDownloader

console = Console(safe_box=True)
hub_app = typer.Typer(
    name="model-hub",
    help="Explore, inspect, install, and manage Hugging Face Transformers models.",
    invoke_without_command=True,
)


@hub_app.callback()
def main_callback(ctx: typer.Context) -> None:
    """Launch interactive Model Hub TUI when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        tui = ModelHubTUI()
        tui.run()


@hub_app.command("list")
def list_installed_models() -> None:
    """List all locally installed Transformers models."""
    registry = ModelRegistry()
    installed = registry.list_installed()

    if not installed:
        console.print("[yellow]No models currently installed. Run 'proton model-hub' to discover models.[/yellow]")
        return

    table = Table(title="Locally Installed Transformers Models", show_header=True, header_style="bold cyan")
    table.add_column("Model ID", style="bold bright_white", width=34)
    table.add_column("Params", style="bold green", width=8)
    table.add_column("Size", style="cyan", width=8)
    table.add_column("Installed Path", style="dim", width=36)
    table.add_column("Default", style="bold", width=9)

    for m in installed:
        is_def = "[bold magenta]★ Default[/bold magenta]" if m.is_default else "[dim]—[/dim]"
        table.add_row(
            m.id,
            m.parameters_display,
            f"{m.size_gb:.1f} GB",
            m.local_path[-34:],
            is_def,
        )

    console.print(table)


@hub_app.command("search")
def search_models(
    query: str = typer.Argument(..., help="Search keyword or model name"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of results to display"),
) -> None:
    """Search Hugging Face models from the terminal."""
    client = HuggingFaceHubClient()
    with console.status(f"[bold cyan]Searching Hugging Face for '{query}'...[/bold cyan]"):
        models, _, _ = client.search_models(query=query, page_size=limit)

    if not models:
        console.print(f"[yellow]No models found matching '{query}'.[/yellow]")
        return

    table = Table(title=f"Hugging Face Search: '{query}'", show_header=True, header_style="bold cyan")
    table.add_column("#", style="bold yellow", width=3)
    table.add_column("Model ID", style="bold bright_white", width=34)
    table.add_column("Params", style="bold green", width=8)
    table.add_column("Size", style="cyan", width=8)
    table.add_column("Downloads", style="dim", width=10)
    table.add_column("License", style="dim", width=12)

    for idx, m in enumerate(models, 1):
        dl_str = f"{m.downloads // 1000}k" if m.downloads >= 1000 else str(m.downloads)
        table.add_row(
            str(idx),
            m.id,
            m.parameters_display,
            f"{m.estimated_size_gb:.1f} GB",
            dl_str,
            m.license[:11],
        )

    console.print(table)


@hub_app.command("install")
def install_model(
    model_id: str = typer.Argument(..., help="Hugging Face model ID (e.g. meta-llama/Llama-3.2-1B-Instruct)"),
    set_default: bool = typer.Option(True, "--default/--no-default", help="Set as default model after installation"),
    trust_remote_code: bool = typer.Option(False, "--trust-remote-code", help="Allow custom remote model code"),
) -> None:
    """Download and install a model from Hugging Face."""
    client = HuggingFaceHubClient()
    downloader = ModelDownloader()
    registry = ModelRegistry()

    with console.status(f"[bold cyan]Querying metadata for '{model_id}'...[/bold cyan]"):
        details = client.get_model_details(model_id)

    if not details:
        console.print(f"[red]Could not find model '{model_id}' on Hugging Face.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Installing {details.id} ({details.estimated_size_gb:.1f} GB)...[/bold cyan]")

    final_path = downloader.download_model(model_id=details.id)

    record = registry.register(
        model_id=details.id,
        local_path=final_path,
        total_bytes=details.safetensors_total_bytes,
        parameters_display=details.parameters_display,
        license=details.license,
        requires_remote_code=trust_remote_code,
        is_default=set_default,
    )

    console.print(f"\n[bold green]✓ Successfully installed '{details.id}' to {record.local_path}![/bold green]")
    if set_default:
        from proton.connection.manager import ConnectionManager
        conn_mgr = ConnectionManager()
        conn_mgr.set_active_connection("transformers")
        console.print(f"[bold magenta]★ '{details.id}' is now Proton's default model (Transformers runtime)![/bold magenta]\n")


@hub_app.command("default")
def set_default_model(
    model_id: str = typer.Argument(..., help="Installed model ID to set as default"),
) -> None:
    """Set an installed Transformers model as the default."""
    registry = ModelRegistry()
    if not registry.is_installed(model_id):
        console.print(f"[red]Model '{model_id}' is not installed locally. Run 'proton model-hub install {model_id}' first.[/red]")
        raise typer.Exit(1)

    registry.set_as_proton_default(model_id)
    from proton.connection.manager import ConnectionManager
    conn_mgr = ConnectionManager()
    conn_mgr.set_active_connection("transformers")
    console.print(f"[bold green]✓ Set '{model_id}' as Proton's default model (Transformers provider).[/bold green]")


@hub_app.command("remove")
def remove_model(
    model_id: str = typer.Argument(..., help="Model ID to remove"),
) -> None:
    """Remove an installed model and free disk space."""
    registry = ModelRegistry()
    rec = registry.get_model(model_id)
    if not rec:
        console.print(f"[yellow]Model '{model_id}' is not in local registry.[/yellow]")
        return

    import shutil
    import os
    if os.path.exists(rec.local_path):
        shutil.rmtree(rec.local_path, ignore_errors=True)
    registry.unregister(model_id)
    console.print(f"[green]✓ Removed '{model_id}'.[/green]")


@hub_app.command("hardware")
def show_hardware() -> None:
    """Inspect system hardware and AI model parameter fit guide."""
    hw = detect_hardware()
    table = Table(title="System Hardware Specifications", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold yellow", width=22)
    table.add_column("Value", style="bold bright_white", width=48)

    table.add_row("Operating System", hw.os_name)
    table.add_row("CPU Architecture", f"{hw.cpu_arch} ({hw.cpu_count_physical} Cores)")
    table.add_row("System RAM", f"{hw.available_ram_gb} GB Available / {hw.total_ram_gb} GB Total")
    table.add_row("GPU / VRAM", f"{hw.cuda_device_name} ({hw.cuda_vram_gb} GB VRAM)" if hw.has_cuda else "None (CPU Mode)")
    table.add_row("Recommended Device", hw.recommended_device.upper())
    table.add_row("Free Disk Space", f"{hw.disk_free_gb} GB Free")

    console.print(table)
