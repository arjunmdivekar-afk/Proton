"""CLI subcommands for Proton Project Knowledge Graph (`proton graph`)."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from proton.graph.engine import ProjectGraphEngine

graph_app = typer.Typer(
    help="Manage and query the Project Knowledge Graph (GraphRAG, Impact Analysis, Callers, Tests).",
    no_args_is_help=False,
)
console = Console(safe_box=True)


@graph_app.callback(invoke_without_command=True)
def default_graph_callback(
    ctx: typer.Context,
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path to inspect"),
) -> None:
    """Display Knowledge Graph status and stats, or run `proton graph build`."""
    if ctx.invoked_subcommand is not None:
        return

    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    engine = ProjectGraphEngine(workspace)
    stats = engine.get_stats()

    if stats.total_nodes == 0:
        console.print("[yellow]Project Knowledge Graph is not built yet.[/yellow]")
        console.print("[dim]Build it now by running:[/dim] [bold bright_white]proton graph build[/bold bright_white]\n")
        return

    table = Table(title="⚛️ Proton Project Knowledge Graph (GraphRAG)", show_header=True, header_style="bold cyan")
    table.add_column("Graph Entity", style="bold", width=25)
    table.add_column("Count", justify="right", style="cyan", width=15)

    table.add_row("Total Code Nodes", str(stats.total_nodes))
    table.add_row("Total Relationship Edges", str(stats.total_edges))
    table.add_row("Modules", str(stats.modules_count))
    table.add_row("Classes", str(stats.classes_count))
    table.add_row("Functions & Methods", str(stats.functions_count))
    table.add_row("Test Cases", str(stats.tests_count))
    table.add_row("Function Call Edges (CALLS)", str(stats.calls_edges_count))
    table.add_row("Inheritance Edges (INHERITS)", str(stats.inherits_edges_count))
    table.add_row("Module Imports (IMPORTS)", str(stats.imports_edges_count))
    table.add_row("Test Mappings (TESTS)", str(stats.tests_edges_count))

    console.print(table)
    console.print(
        "\n[dim]Query relationships using:\n"
        "  • `proton graph impact <symbol>` — Blast radius analysis\n"
        "  • `proton graph callers <symbol>` — Find all callers\n"
        "  • `proton graph tests <symbol>`   — Find all unit tests[/dim]\n"
    )


@graph_app.command("build")
def build_graph_cmd(
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path to index"),
) -> None:
    """Extract AST symbols and construct the project knowledge graph."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    engine = ProjectGraphEngine(workspace)

    with console.status("[cyan]Analyzing AST and building project knowledge graph...[/cyan]", spinner="dots"):
        stats = engine.build_graph()

    console.print(
        Panel.fit(
            f"[bold green]✓ Project Knowledge Graph Built Successfully![/bold green]\n\n"
            f"• [bold]Nodes Indexed:[/bold] [cyan]{stats.total_nodes}[/cyan] ({stats.modules_count} modules, {stats.classes_count} classes, {stats.functions_count} functions, {stats.tests_count} tests)\n"
            f"• [bold]Relationship Edges:[/bold] [cyan]{stats.total_edges}[/cyan] ({stats.calls_edges_count} calls, {stats.inherits_edges_count} inheritance, {stats.tests_edges_count} test links)\n"
            f"• [bold]Database:[/bold] [dim]{engine.db_path}[/dim]\n\n"
            f"[dim]Try running impact analysis:[/dim] [bold bright_white]proton graph impact validate_path[/bold bright_white]",
            border_style="green",
        )
    )


@graph_app.command("index")
def index_graph_cmd(
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path to index"),
) -> None:
    """Alias for `proton graph build`."""
    build_graph_cmd(target_path)


@graph_app.command("impact")
def impact_graph_cmd(
    symbol: str = typer.Argument(..., help="Function, Class, or Module symbol to analyze"),
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path"),
) -> None:
    """Analyze blast radius: 'What will break if I change this function/class?'"""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    engine = ProjectGraphEngine(workspace)
    rep = engine.impact_analysis(symbol)

    if not rep.direct_callers and not rep.indirect_callers and not rep.affecting_tests:
        # If DB is empty, auto-build first
        if not engine.nodes:
            engine.build_graph()
            rep = engine.impact_analysis(symbol)

    tree = Tree(f"[bold cyan]IMPACT ANALYSIS: {rep.target_symbol}[/bold cyan] [dim]({rep.file_path})[/dim]")
    tree.add(f"[bold]Total Blast Radius:[/bold] [bold red]{rep.total_blast_radius} affected entities[/bold red]")

    # Direct Callers
    callers_node = tree.add(f"[bold green]Direct Callers ({len(rep.direct_callers)}):[/bold green]")
    if rep.direct_callers:
        for c in rep.direct_callers[:10]:
            callers_node.add(f"[cyan]{c}[/cyan]")
    else:
        callers_node.add("[dim]No direct callers detected[/dim]")

    # Indirect Callers
    if rep.indirect_callers:
        ind_node = tree.add(f"[bold yellow]Indirect Callers / Downstream ({len(rep.indirect_callers)}):[/bold yellow]")
        for c in rep.indirect_callers[:10]:
            ind_node.add(f"[dim]{c}[/dim]")

    # Subclasses
    if rep.inheriting_classes:
        inh_node = tree.add(f"[bold magenta]Subclasses Inheriting ({len(rep.inheriting_classes)}):[/bold magenta]")
        for c in rep.inheriting_classes:
            inh_node.add(f"[magenta]{c}[/magenta]")

    # Affecting Tests
    tests_node = tree.add(f"[bold bright_cyan]Tests to Run ({len(rep.affecting_tests)}):[/bold bright_cyan]")
    if rep.affecting_tests:
        for t in rep.affecting_tests[:10]:
            tests_node.add(f"[green]✓ {t}[/green]")
    else:
        tests_node.add("[yellow]⚠️ No direct unit test coverage detected[/yellow]")

    # Callees
    if rep.callees:
        callee_node = tree.add(f"[bold]Calls Downstream ({len(rep.callees)}):[/bold]")
        for cl in rep.callees[:8]:
            callee_node.add(f"[dim]{cl}[/dim]")

    console.print()
    console.print(
        Panel(
            tree,
            title="[bold red]⚡ Change Impact & Blast Radius Report[/bold red]",
            border_style="red" if rep.total_blast_radius > 5 else "cyan",
        )
    )
    console.print(f"[bold]Summary:[/bold] {rep.summary}\n")


@graph_app.command("callers")
def callers_graph_cmd(
    symbol: str = typer.Argument(..., help="Symbol to find callers for"),
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path"),
) -> None:
    """List all functions or modules calling a given symbol."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    engine = ProjectGraphEngine(workspace)
    rep = engine.impact_analysis(symbol)

    if not rep.direct_callers and not rep.indirect_callers:
        console.print(f"[yellow]No callers found for '{symbol}'.[/yellow]")
        return

    table = Table(title=f"Callers of '{symbol}'", show_header=True, header_style="bold cyan")
    table.add_column("Caller Symbol", style="bold cyan")
    table.add_column("Call Type", style="magenta")

    for c in rep.direct_callers:
        table.add_row(c, "Direct Call")
    for c in rep.indirect_callers:
        table.add_row(c, "Indirect (Transitive)")

    console.print(table)


@graph_app.command("tests")
def tests_graph_cmd(
    symbol: str = typer.Argument(..., help="Symbol to find tests for"),
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path"),
) -> None:
    """List all automated test functions targeting a given symbol."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    engine = ProjectGraphEngine(workspace)
    rep = engine.impact_analysis(symbol)

    if not rep.affecting_tests:
        console.print(f"[yellow]No automated unit tests found targeting '{symbol}'.[/yellow]")
        return

    table = Table(title=f"Automated Tests Covering '{symbol}'", show_header=True, header_style="bold green")
    table.add_column("Test Function", style="bold green")

    for t in rep.affecting_tests:
        table.add_row(t)

    console.print(table)
