"""CLI command to launch Proton Server & REST API (`proton server`)."""

import socket
import uvicorn
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager

console = Console(safe_box=True)


def get_wifi_lan_ip() -> str:
    """Detect machine's primary WiFi / LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def launch_server(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-h",
        help="Bind host address (e.g. 0.0.0.0, 127.0.0.1, or 'lan'/'wifi' to host on connected WiFi)",
    ),
    port: int = typer.Option(8787, "--port", "-p", help="Bind port number"),
    lan: bool = typer.Option(
        False,
        "--lan",
        "--wifi",
        help="Host on connected WiFi so any device on the network can access http://<WiFi_IP>:<port>",
    ),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload on code change"),
) -> None:
    """Launch Proton Autonomous AI Server & REST/SSE API."""
    config_mgr = ConfigManager()
    conn_mgr = ConnectionManager()
    active_conn = conn_mgr.get_active_connection()

    wifi_ip = get_wifi_lan_ip()

    # Determine bind host and display addresses
    if lan or (host and host.lower() in ("0.0.0.0", "lan", "wifi", "auto", "all")):
        bind_host = "0.0.0.0"
        is_lan_hosted = True
    elif host:
        bind_host = host
        is_lan_hosted = (bind_host == "0.0.0.0")
    else:
        # Default to 0.0.0.0 to enable both localhost and WiFi access out of the box
        bind_host = "0.0.0.0"
        is_lan_hosted = True

    local_url = f"http://127.0.0.1:{port}"
    network_url = f"http://{wifi_ip}:{port}"
    docs_local = f"http://127.0.0.1:{port}/docs"
    docs_network = f"http://{wifi_ip}:{port}/docs"

    banner_lines = [
        f"[bold bright_white]🏠 Local Access:[/bold bright_white] [bold cyan]{local_url}[/bold cyan]",
    ]

    if is_lan_hosted and wifi_ip != "127.0.0.1":
        banner_lines.append(
            f"[bold bright_white]📶 WiFi / LAN Access:[/bold bright_white] [bold green]{network_url}[/bold green] [dim](Anyone on this WiFi)[/dim]"
        )
        banner_lines.append(
            f"[bold bright_white]📚 Interactive Swagger UI:[/bold bright_white] [bold yellow]{docs_network}[/bold yellow]"
        )
    else:
        banner_lines.append(
            f"[bold bright_white]📚 Interactive Swagger UI:[/bold bright_white] [bold yellow]{docs_local}[/bold yellow]"
        )

    banner_lines.append(
        f"[bold bright_white]🧠 Active Provider:[/bold bright_white] [magenta]{active_conn.provider.value if active_conn else 'None'}[/magenta] "
        f"([dim]{active_conn.base_url if active_conn else ''}[/dim])"
    )
    banner_lines.append(
        f"[bold bright_white]🤖 Active Model:[/bold bright_white] [yellow]{config_mgr.config.active_model or 'default'}[/yellow]"
    )

    console.print()
    console.print(
        Panel(
            "\n".join(banner_lines),
            title="[bold cyan]⚛️ PROTON AUTONOMOUS AI SERVER v2.4.4[/bold cyan]",
            subtitle=f"[dim]Binding on [bold]{bind_host}:{port}[/bold] — WiFi Network Sharing Active[/dim]" if is_lan_hosted else f"[dim]Binding on [bold]{bind_host}:{port}[/bold][/dim]",
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
        host=bind_host,
        port=port,
        reload=reload,
        log_level="info",
    )
