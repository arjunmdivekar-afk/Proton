"""CLI commands for Proton Model & Provider Benchmark (`proton benchmark`)."""

import asyncio
import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from proton.benchmark.runner import BenchmarkRunner
from proton.benchmark.models import BenchmarkReport
from proton.core.config import get_proton_home

benchmark_app = typer.Typer(
    help="Benchmark LLM models and providers across latency, tokens/sec, tool calling, RAG, coding, planning, and error recovery.",
    no_args_is_help=False,
)
console = Console(safe_box=True)

GRADE_COLORS = {
    "A+": "bold green",
    "A": "green",
    "B": "cyan",
    "C": "yellow",
    "D": "magenta",
    "F": "bold red",
}


@benchmark_app.callback(invoke_without_command=True)
def default_benchmark_callback(
    ctx: typer.Context,
    quick: bool = typer.Option(False, "--quick", "-q", help="Run fast 3-stage benchmark"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Run Proton LLM Benchmark Suite."""
    if ctx.invoked_subcommand is not None:
        return

    runner = BenchmarkRunner(quick=quick)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Running Proton Benchmark Battery...[/cyan]", total=7 if not quick else 3)

        def on_progress(step_name: str, current: int, total: int) -> None:
            progress.update(task, description=f"[cyan]Testing {step_name}...[/cyan]", completed=current)

        report = asyncio.run(runner.run_benchmark(progress_callback=on_progress))

    if json_mode:
        console.print_json(report.model_dump_json())
        return

    _render_benchmark_report(report)


@benchmark_app.command("run")
def run_benchmark_cmd(
    quick: bool = typer.Option(False, "--quick", "-q", help="Run fast 3-stage benchmark"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Explicitly trigger full benchmark run."""
    default_benchmark_callback(typer.Context(typer.main.get_command(benchmark_app)), quick=quick, json_mode=json_mode)


@benchmark_app.command("history")
def history_benchmark_cmd() -> None:
    """View past benchmark results and model performance history."""
    history_path = get_proton_home() / "benchmarks.json"
    if not history_path.exists():
        console.print("[yellow]No past benchmark records found.[/yellow]")
        console.print("[dim]Run a benchmark with:[/dim] [bold bright_white]proton benchmark[/bold bright_white]\n")
        return

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except Exception:
        data = []

    if not data:
        console.print("[yellow]No past benchmark records found.[/yellow]")
        return

    table = Table(title="⚛️ Proton Benchmark History", show_header=True, header_style="bold cyan")
    table.add_column("Timestamp", style="dim", width=17)
    table.add_column("Model ID", style="bold cyan", width=26)
    table.add_column("Provider", width=12)
    table.add_column("Speed", justify="right", style="yellow", width=12)
    table.add_column("Score", justify="right", style="bold", width=10)
    table.add_column("Grade", justify="center", width=8)

    for item in reversed(data[-10:]):
        ts = item.get("timestamp", "")[:16].replace("T", " ")
        g = item.get("grade", "B")
        g_color = GRADE_COLORS.get(g, "white")
        table.add_row(
            ts,
            item.get("model_id", "Unknown")[:24],
            item.get("provider", "local"),
            f"{item.get('tokens_per_sec', 0)} tok/s",
            f"{item.get('overall_score', 0)} / 100",
            f"[{g_color}]{g}[/{g_color}]",
        )

    console.print(table)


def _render_benchmark_report(report: BenchmarkReport) -> None:
    grade_color = GRADE_COLORS.get(report.grade, "white")

    # Header Panel
    header_text = (
        f"[bold bright_white]Model:[/bold bright_white] [cyan]{report.model_id}[/cyan]   "
        f"[bold bright_white]Provider:[/bold bright_white] [magenta]{report.provider}[/magenta]   "
        f"[bold bright_white]Base URL:[/bold bright_white] [dim]{report.base_url}[/dim]\n"
        f"[bold bright_white]TTFT:[/bold bright_white] [yellow]{report.ttft_ms} ms[/yellow]   "
        f"[bold bright_white]Throughput:[/bold bright_white] [bold yellow]{report.tokens_per_sec} tokens/sec[/bold yellow]   "
        f"[bold bright_white]Overall Rating:[/bold bright_white] [{grade_color}][{report.grade}] {report.overall_score} / 100[/{grade_color}]"
    )
    console.print()
    console.print(
        Panel(
            header_text,
            title="[bold cyan]⚡ Proton LLM & Provider Benchmark Results[/bold cyan]",
            border_style="cyan",
        )
    )

    # Test Results Table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Capability Dimension", style="bold", width=30)
    table.add_column("Result", justify="center", width=10)
    table.add_column("Score", justify="right", width=10)
    table.add_column("Latency", justify="right", style="dim", width=12)
    table.add_column("Assessment Details", width=38)

    for s in report.scores:
        status_str = "[green]PASS ✓[/green]" if s.passed else "[red]FAIL ✗[/red]"
        score_color = "green" if s.score >= 80 else ("yellow" if s.score >= 50 else "red")
        table.add_row(
            s.name,
            status_str,
            f"[{score_color}]{s.score}%[/{score_color}]",
            f"{round(s.duration_ms)} ms",
            s.details,
        )

    console.print(table)

    # Readiness Banner
    console.print(
        f"\n[bold]Autonomous Agent Readiness:[/bold] [{grade_color}]{report.agent_readiness}[/{grade_color}]"
    )

    if report.recommendations:
        console.print("[bold]Recommendations & Observations:[/bold]")
        for r in report.recommendations:
            console.print(f"  • {r}")
    console.print()
