"""CLI subcommands for Proton Repository & Codebase Inspection (`proton inspect`)."""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from proton.inspect.analyzer import RepoAnalyzer

inspect_app = typer.Typer(
    help="Deep repository and codebase inspection (architecture, security, dependencies, tests, performance).",
    no_args_is_help=False,
)
console = Console(safe_box=True)


@inspect_app.callback(invoke_without_command=True)
def default_inspect_callback(
    ctx: typer.Context,
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Directory path to inspect (defaults to current workspace)"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Run full repository inspection: language, framework, dependencies, architecture, tests, and security."""
    if ctx.invoked_subcommand is not None:
        return

    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    report = analyzer.inspect_all()

    if json_mode:
        console.print_json(report.model_dump_json())
        return

    # Render Project Tree View
    tree = Tree(f"[bold cyan]PROJECT: {report.project_name}[/bold cyan] [dim]({report.workspace_root})[/dim]")

    # 1. Language Detection
    lang_str = ", ".join(f"{l.name} ({l.percentage}%)" for l in report.languages[:4]) or "Unknown"
    tree.add(f"[bold]Language detection:[/bold] [green]{lang_str}[/green]")

    # 2. Framework Detection
    if report.frameworks:
        fw_str = ", ".join(f"{f.name} [dim]({f.category})[/dim]" for f in report.frameworks)
    else:
        fw_str = "[dim]Standard Library / Generic[/dim]"
    tree.add(f"[bold]Framework detection:[/bold] {fw_str}")

    # 3. Dependencies
    dep_str = f"{report.dependencies.total_count} direct packages [dim]({report.dependencies.package_manager})[/dim]"
    tree.add(f"[bold]Dependencies:[/bold] [cyan]{dep_str}[/cyan]")

    # 4. Architecture
    arch_node = tree.add(f"[bold]Architecture:[/bold] [magenta]{report.architecture.pattern}[/magenta]")
    if report.architecture.layers:
        arch_node.add(f"[dim]Identified layers:[/dim] {', '.join(report.architecture.layers)}")

    # 5. Entry Points
    entry_str = ", ".join(report.entry_points[:3]) if report.entry_points else "[dim]None detected[/dim]"
    tree.add(f"[bold]Entry points:[/bold] [yellow]{entry_str}[/yellow]")

    # 6. Test Framework
    test_str = f"{report.test_framework.framework} [dim]({report.test_framework.test_files_count} test files)[/dim]"
    tree.add(f"[bold]Test framework:[/bold] [bright_cyan]{test_str}[/bright_cyan]")

    # 7. Git Status
    if report.git_status.get("is_git_repo"):
        clean_str = "[green]Clean (No uncommitted changes)[/green]" if report.git_status.get("is_clean") else f"[yellow]{report.git_status.get('uncommitted_files_count')} uncommitted files[/yellow]"
        git_str = f"Branch [cyan]{report.git_status.get('branch')}[/cyan], {clean_str}"
    else:
        git_str = "[dim]Not a git repository[/dim]"
    tree.add(f"[bold]Git status:[/bold] {git_str}")

    # 8. Documentation
    doc_str = ", ".join(report.documentation) if report.documentation else "[dim]Missing README / docs[/dim]"
    tree.add(f"[bold]Documentation:[/bold] [blue]{doc_str}[/blue]")

    # 9. Environment
    env_str = f"Python {report.environment.get('python_version')} [dim](Platform: {report.environment.get('platform')})[/dim]"
    tree.add(f"[bold]Environment:[/bold] {env_str}")

    # 10. Potential Problems
    if report.potential_problems:
        prob_node = tree.add("[bold red]Potential problems:[/bold red]")
        for p in report.potential_problems:
            prob_node.add(f"[{p.severity}] [bold]{p.title}:[/bold] {p.description}")
    else:
        tree.add("[bold green]Potential problems:[/bold green] [green]✓ None detected (Healthy repository state)[/green]")

    console.print()
    console.print(
        Panel(
            tree,
            title="[bold cyan]⚛️ Proton Repository & Architecture Inspection[/bold cyan]",
            border_style="cyan",
            expand=False,
        )
    )
    console.print(
        "[dim]Tip: Run specialized audits with `proton inspect security`, `proton inspect architecture`, "
        "`proton inspect dependencies`, `proton inspect tests`, or `proton inspect performance`.[/dim]\n"
    )


@inspect_app.command("security")
def inspect_security_cmd(
    target_path: Optional[str] = typer.Argument(None, help="Directory path to inspect"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Audit codebase for hardcoded secrets, vulnerability patterns, and security posture."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    sec = analyzer.audit_security()

    if json_mode:
        console.print_json(sec.model_dump_json())
        return

    table = Table(title="Proton Security Audit Report", show_header=True, header_style="bold cyan")
    table.add_column("Audit Metric", style="bold", width=25)
    table.add_column("Result", width=55)

    score_color = "green" if sec.score >= 80 else ("yellow" if sec.score >= 60 else "red")
    table.add_row("Security Score", f"[{score_color}]{sec.score} / 100[/{score_color}]")
    table.add_row("Hardcoded Secrets", f"{len(sec.hardcoded_secrets_found)} detected")
    table.add_row("Security Documentation", ", ".join(sec.security_files) or "[yellow]Missing SECURITY.md[/yellow]")

    console.print(table)

    if sec.hardcoded_secrets_found:
        console.print("\n[bold red]⚠️ Potential Exposed Secrets:[/bold red]")
        for s in sec.hardcoded_secrets_found:
            console.print(f"  • [red]{s}[/red]")
    else:
        console.print("\n[bold green]✓ No hardcoded secrets or API keys detected in workspace.[/bold green]")


@inspect_app.command("architecture")
def inspect_architecture_cmd(
    target_path: Optional[str] = typer.Argument(None, help="Directory path to inspect"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Analyze structural patterns, package layout, layers, and entry points."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    arch = analyzer.inspect_architecture()

    if json_mode:
        console.print_json(arch.model_dump_json())
        return

    table = Table(title="Proton Architecture Analysis", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="bold", width=20)
    table.add_column("Details", width=60)

    table.add_row("Design Pattern", f"[magenta]{arch.pattern}[/magenta]")
    table.add_row("Core Modules", ", ".join(arch.core_modules) or "[dim]Flat root layout[/dim]")
    table.add_row("Detected Layers", ", ".join(arch.layers) or "[dim]Monolithic structure[/dim]")
    table.add_row("Entry Points", "\n".join(arch.entry_points) or "[dim]None standard found[/dim]")

    console.print(table)


@inspect_app.command("dependencies")
def inspect_dependencies_cmd(
    target_path: Optional[str] = typer.Argument(None, help="Directory path to inspect"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Inspect declared dependencies, manifest files, and package managers."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    deps = analyzer.inspect_dependencies()

    if json_mode:
        console.print_json(deps.model_dump_json())
        return

    table = Table(title=f"Dependencies ({deps.total_count} packages via {deps.package_manager})", show_header=True, header_style="bold cyan")
    table.add_column("Package Name", style="bold cyan")
    table.add_column("Version Constraint", style="dim")
    table.add_column("Type", style="magenta")

    for d in deps.direct_dependencies:
        table.add_row(d.name, d.version_spec or "*", "Dev" if d.is_dev else "Runtime")

    console.print(table)


@inspect_app.command("tests")
def inspect_tests_cmd(
    target_path: Optional[str] = typer.Argument(None, help="Directory path to inspect"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Audit automated test suites, test files count, and CI configurations."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    tests = analyzer.inspect_tests()

    if json_mode:
        console.print_json(tests.model_dump_json())
        return

    table = Table(title="Test Suite Audit", show_header=True, header_style="bold cyan")
    table.add_column("Attribute", style="bold", width=25)
    table.add_column("Status", width=50)

    table.add_row("Framework", f"[cyan]{tests.framework}[/cyan]")
    table.add_row("Test Files Count", str(tests.test_files_count))
    table.add_row("Test Directories", ", ".join(tests.test_directories) or "[yellow]None found[/yellow]")
    table.add_row("CI Pipeline Config", "[green]Yes[/green]" if tests.has_ci_config else "[dim]No CI config found[/dim]")

    console.print(table)


@inspect_app.command("performance")
def inspect_performance_cmd(
    target_path: Optional[str] = typer.Argument(None, help="Directory path to inspect"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Analyze repo size, heavy assets, and potential runtime bottlenecks."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    perf = analyzer.audit_performance()

    if json_mode:
        console.print_json(perf.model_dump_json())
        return

    console.print(f"[bold cyan]Total Workspace Size:[/bold cyan] [bold bright_white]{perf.total_repo_size_mb} MB[/bold bright_white]\n")
    if perf.large_files:
        table = Table(title="Largest Files in Workspace (> 500 KB)", show_header=True, header_style="bold cyan")
        table.add_column("File Path", style="cyan")
        table.add_column("Size (KB)", justify="right", style="yellow")

        for lf in perf.large_files:
            table.add_row(lf["path"], str(lf["size_kb"]))
        console.print(table)
    else:
        console.print("[green]✓ No oversized files (> 500 KB) detected in repository.[/green]")
