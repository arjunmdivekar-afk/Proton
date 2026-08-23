"""CLI command to launch Proton Server & REST API (`proton server`)."""

import uvicorn
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager

console = Console(safe_box=True)


def launch_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host address"),
    port: int = typer.Option(8787, "--port", "-p", help="Bind port number"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload on code change"),
) -> None:
    """Launch Proton Autonomous AI Server & REST/SSE API."""
    config_mgr = ConfigManager()
    conn_mgr = ConnectionManager()
    active_conn = conn_mgr.get_active_connection()

    base_url = f"http://{host}:{port}"
    docs_url = f"http://{host}:{port}/docs"

    banner_text = (
        f"[bold bright_white]⚡ Proton Server Running:[/bold bright_white] [bold cyan]{base_url}[/bold cyan]\n"
        f"[bold bright_white]📚 Interactive Swagger UI:[/bold bright_white] [bold green]{docs_url}[/bold green]\n"
        f"[bold bright_white]🧠 Active Provider:[/bold bright_white] [magenta]{active_conn.provider.value if active_conn else 'None'}[/magenta] "
        f"([dim]{active_conn.base_url if active_conn else ''}[/dim])\n"
        f"[bold bright_white]🤖 Active Model:[/bold bright_white] [yellow]{config_mgr.config.active_model or 'default'}[/yellow]"
    )

    console.print()
    console.print(
        Panel(
            banner_text,
            title="[bold cyan]⚛️ PROTON AUTONOMOUS AI SERVER v2.4.4[/bold cyan]",
            border_style="cyan",
        )
    )

    table = Table(title="Core REST & SSE API Endpoints", show_header=True, header_style="bold cyan")
    table.add_column("HTTP Method", style="bold yellow", width=12)
    table.add_column("Endpoint Route", style="bold bright_white", width=28)
    table.add_column("Capability / Description", style="dim", width=42)

    table.add_row("POST", "/v1/chat", "Token streaming (SSE) & chat completion")
    table.add_row("POST", "/v1/agents/run", "Launch 10-stage Max Autonomous Agent")
    table.add_row("POST / GET", "/v1/tasks", "Stateful engineering tasks & checkpoints")
    table.add_row("GET", "/v1/graph/impact", "GraphRAG symbol blast radius analysis")
    table.add_row("POST / GET", "/v1/memory", "Categorized domain memory (PROJECT, DECISION)")
    table.add_row("POST", "/v1/rag/search", "Hybrid BM25 and vector knowledge query")
    table.add_row("GET", "/v1/inspect", "Deep repository structural inspection")
    table.add_row("POST", "/v1/benchmark/run", "8-dimension model performance test")
    table.add_row("POST", "/v1/security/test", "Continuous security defense verification")
    table.add_row("POST", "/v1/tools/execute", "Deterministic tool invocation with sandbox")
    table.add_row("GET", "/v1/health", "Server status, version, and health metrics")

    console.print(table)
    console.print("\n[dim]Press [bold]Ctrl+C[/bold] to stop the server.[/dim]\n")

    uvicorn.run(
        "proton.server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
