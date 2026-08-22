"""CLI commands for connection management (`proton connection`)."""

import asyncio
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from proton.connection.manager import ConnectionManager
from proton.connection.schema import ConnectionProfile, ProviderType, ConnectionStatus
from proton.connection.wizard import run_connection_wizard


conn_app = typer.Typer(help="Manage AI connections (LM Studio, Ollama, OpenAI-compatible)")
console = Console()


@conn_app.callback(invoke_without_command=True)
def default_connection_command(ctx: typer.Context) -> None:
    """Run interactive connection wizard if no subcommand specified."""
    if ctx.invoked_subcommand is None:
        asyncio.run(run_connection_wizard())


@conn_app.command("list")
def list_connections_cmd() -> None:
    """List all configured model provider connections."""
    mgr = ConnectionManager()
    active_id = mgr.config_mgr.config.active_connection
    connections = mgr.list_connections()

    table = Table(title="Proton AI Connections", show_header=True, header_style="bold cyan")
    table.add_column("Status", style="dim", width=12)
    table.add_column("ID / Name", style="bold")
    table.add_column("Provider")
    table.add_column("Endpoint")
    table.add_column("Models", justify="right")
    table.add_column("Latency", justify="right")

    for conn in connections:
        is_active = conn.id == active_id
        prefix = "* [green](active)[/green] " if is_active else "  "
        status_chip = (
            "[green][ONLINE][/green]" if conn.status == ConnectionStatus.CONNECTED
            else "[red][OFFLINE][/red]"
        )
        latency_str = f"{conn.latency_ms:.1f} ms" if conn.latency_ms else "-"
        models_count = str(len(conn.discovered_models))

        table.add_row(
            status_chip,
            f"{prefix}{conn.name} [dim]({conn.id})[/dim]",
            conn.provider.value,
            conn.base_url,
            models_count,
            latency_str,
        )

    console.print(table)


@conn_app.command("add")
def add_connection_cmd(
    provider: str = typer.Argument(..., help="Provider type: lmstudio, ollama, openai_compatible"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Connection name"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server IP address or hostname (e.g. 192.168.1.50)"),
    port: int = typer.Option(1234, "--port", "-p", help="Server port"),
    protocol: str = typer.Option("http", "--protocol", help="http or https"),
    base_path: str = typer.Option("/v1", "--base-path", help="API base path"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key if required"),
    test: bool = typer.Option(True, "--test/--no-test", help="Test connection immediately"),
) -> None:
    """Add a new model provider connection (e.g. `proton connection add lmstudio --host 192.168.1.50 --port 1234`)."""
    mgr = ConnectionManager()
    try:
        ptype = ProviderType(provider.lower())
    except ValueError:
        ptype = ProviderType.LMSTUDIO

    cname = name or f"{ptype.value.title()} ({host}:{port})"
    cid = cname.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(":", "-")

    profile = ConnectionProfile(
        id=cid,
        name=cname,
        provider=ptype,
        host=host,
        port=port,
        protocol=protocol,
        base_path=base_path,
        api_key=api_key,
    )
    mgr.add_connection(profile)
    console.print(f"[green]Saved connection '{cid}' ({profile.base_url})[/green]")

    if test:
        console.print(f"[yellow]Testing connection to {profile.base_url}...[/yellow]")
        res = asyncio.run(mgr.test_connection(cid))
        if res.success:
            console.print(f"[bold green]✓ Successfully connected in {res.latency_ms:.1f}ms![/bold green]")
            if res.discovered_models:
                console.print(f"[green]Discovered {len(res.discovered_models)} models:[/green] {', '.join(res.discovered_models)}")
                mgr.config_mgr.set_active_model(res.discovered_models[0])
            mgr.set_active_connection(cid)
            console.print(f"[bold green]Set '{cid}' as active connection.[/bold green]")
        else:
            console.print(f"[bold red]✗ Connection test failed:[/bold red] {res.error_message}")
            if res.remediation_advice:
                console.print(f"[dim]{res.remediation_advice}[/dim]")


@conn_app.command("test")
def test_connection_cmd(
    connection_id: Optional[str] = typer.Argument(None, help="Connection ID to test (default: active connection)")
) -> None:
    """Test connectivity to a specific or active model connection."""
    mgr = ConnectionManager()
    cid = connection_id or mgr.config_mgr.config.active_connection
    console.print(f"[yellow]Testing connection '{cid}'...[/yellow]")
    res = asyncio.run(mgr.test_connection(cid))
    if res.success:
        console.print(f"[bold green]✓ Connected ({res.latency_ms:.1f}ms)![/bold green]")
        console.print(f"Discovered models: {', '.join(res.discovered_models) or 'None'}")
    else:
        console.print(f"[bold red]✗ Failed:[/bold red] {res.error_message}")
        if res.remediation_advice:
            console.print(f"[dim]{res.remediation_advice}[/dim]")


@conn_app.command("use")
def use_connection_cmd(
    connection_id: str = typer.Argument(..., help="Connection ID to set active")
) -> None:
    """Set the active model provider connection."""
    mgr = ConnectionManager()
    if mgr.set_active_connection(connection_id):
        console.print(f"[bold green]Active connection switched to: {connection_id}[/bold green]")
    else:
        console.print(f"[bold red]Connection '{connection_id}' not found. Run `proton connection list`.[/bold red]")
