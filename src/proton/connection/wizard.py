"""Interactive Connection Wizard for Proton terminal interface."""

import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from proton.connection.manager import ConnectionManager
from proton.connection.schema import ConnectionProfile, ProviderType, ConnectionStatus


async def run_connection_wizard(manager: Optional[ConnectionManager] = None) -> None:
    """Run interactive CLI wizard for managing model provider connections."""
    console = Console()
    mgr = manager or ConnectionManager()

    console.print(
        Panel.fit(
            "[bold cyan]PROTON CONNECTION MANAGER[/bold cyan]\n"
            "[dim]Configure LM Studio (Local / LAN IP), Ollama, and OpenAI-compatible inference servers[/dim]",
            border_style="cyan",
        )
    )

    table = Table(title="Configured AI Connections", show_header=True, header_style="bold magenta")
    table.add_column("Status", style="dim", width=12)
    table.add_column("ID / Name", style="bold")
    table.add_column("Provider")
    table.add_column("Endpoint")
    table.add_column("Models", justify="right")
    table.add_column("Latency", justify="right")

    active_id = mgr.config_mgr.config.active_connection
    connections = mgr.list_connections()

    for conn in connections:
        is_active = conn.id == active_id
        prefix = "★ [green](active)[/green] " if is_active else "  "
        status_chip = (
            "[green]● Connected[/green]" if conn.status == ConnectionStatus.CONNECTED
            else "[red]○ Offline[/red]"
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
    console.print("\n[bold]Actions:[/bold]")
    console.print("1. Add LM Studio connection (Local or LAN IP)")
    console.print("2. Add Ollama connection")
    console.print("3. Add OpenAI-compatible connection")
    console.print("4. Test connection & discover models")
    console.print("5. Set active connection")
    console.print("6. Remove a connection")
    console.print("0. Back / Exit")

    choice = Prompt.ask("\nSelect action", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")

    if choice == "0":
        return

    if choice in ("1", "2", "3"):
        provider = (
            ProviderType.LMSTUDIO if choice == "1"
            else ProviderType.OLLAMA if choice == "2"
            else ProviderType.OPENAI_COMPATIBLE
        )
        default_port = 1234 if provider == ProviderType.LMSTUDIO else (11434 if provider == ProviderType.OLLAMA else 8000)
        default_name = f"LM Studio Server" if provider == ProviderType.LMSTUDIO else f"{provider.value.title()} Server"

        console.print(f"\n[bold green]Configuring new {provider.value.upper()} connection[/bold green]")
        name = Prompt.ask("Connection name", default=default_name)
        cid = name.lower().replace(" ", "-").replace(".", "-")
        host = Prompt.ask("Server IP / Hostname (e.g. 192.168.1.50 or 127.0.0.1)", default="127.0.0.1")
        port_str = Prompt.ask("Port", default=str(default_port))
        port = int(port_str)
        protocol = Prompt.ask("Protocol", choices=["http", "https"], default="http")
        base_path = Prompt.ask("Base Path", default="/v1")
        api_key = Prompt.ask("API Key (optional / press Enter to skip)", default="") or None

        profile = ConnectionProfile(
            id=cid,
            name=name,
            provider=provider,
            host=host,
            port=port,
            protocol=protocol,
            base_path=base_path,
            api_key=api_key,
        )

        console.print(f"\n[yellow]Testing connection to {profile.base_url}...[/yellow]")
        mgr.add_connection(profile)
        test_res = await mgr.test_connection(profile.id)

        if test_res.success:
            console.print(f"[bold green]✓ Successfully connected in {test_res.latency_ms:.1f}ms![/bold green]")
            if test_res.discovered_models:
                console.print(f"[green]Discovered {len(test_res.discovered_models)} models:[/green]")
                for m in test_res.discovered_models:
                    console.print(f"  • [cyan]{m}[/cyan]")
            if Confirm.ask("\nSet as active connection?", default=True):
                mgr.set_active_connection(profile.id)
                if test_res.discovered_models:
                    mgr.config_mgr.set_active_model(test_res.discovered_models[0])
                    console.print(f"[green]Active model set to: {test_res.discovered_models[0]}[/green]")
        else:
            console.print(f"[bold red]✗ Connection test failed:[/bold red] {test_res.error_message}")
            if test_res.remediation_advice:
                console.print(f"[dim]{test_res.remediation_advice}[/dim]")
            if not Confirm.ask("Save profile anyway?", default=False):
                mgr.remove_connection(profile.id)

    elif choice == "4":
        conn_ids = [c.id for c in connections]
        if not conn_ids:
            console.print("[red]No connections configured.[/red]")
            return
        target_id = Prompt.ask("Select connection to test", choices=conn_ids)
        console.print(f"[yellow]Testing connection '{target_id}'...[/yellow]")
        res = await mgr.test_connection(target_id)
        if res.success:
            console.print(f"[bold green]✓ Connected ({res.latency_ms:.1f}ms)![/bold green]")
            console.print(f"Discovered models: {', '.join(res.discovered_models) or 'None'}")
        else:
            console.print(f"[bold red]✗ Failed:[/bold red] {res.error_message}")
            if res.remediation_advice:
                console.print(f"[dim]{res.remediation_advice}[/dim]")

    elif choice == "5":
        conn_ids = [c.id for c in connections]
        if not conn_ids:
            console.print("[red]No connections configured.[/red]")
            return
        target_id = Prompt.ask("Select connection to activate", choices=conn_ids)
        mgr.set_active_connection(target_id)
        console.print(f"[bold green]Active connection set to '{target_id}'[/bold green]")

    elif choice == "6":
        conn_ids = [c.id for c in connections]
        if not conn_ids:
            console.print("[red]No connections configured.[/red]")
            return
        target_id = Prompt.ask("Select connection to remove", choices=conn_ids)
        if Confirm.ask(f"Are you sure you want to remove '{target_id}'?", default=False):
            mgr.remove_connection(target_id)
            console.print(f"[green]Removed connection '{target_id}'[/green]")
