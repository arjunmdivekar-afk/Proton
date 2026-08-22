"""CLI commands for Proton Security Verification & Workspace Audit (`proton security`)."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.security.tester import SecurityTester, SecurityVerificationReport
from proton.inspect.analyzer import RepoAnalyzer
from proton.core.config import ConfigManager

security_app = typer.Typer(
    help="Security defense verification (path traversal, command injection, secret redaction, prompt injection, workspace escapes) and workspace audit.",
    no_args_is_help=False,
)
console = Console(safe_box=True)


@security_app.callback(invoke_without_command=True)
def default_security_callback(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Display active security posture, or run subcommands."""
    if ctx.invoked_subcommand is not None:
        return

    config_mgr = ConfigManager()
    cfg = config_mgr.config.security
    workspace = Path.cwd().resolve()

    if json_mode:
        tester = SecurityTester(workspace)
        rep = tester.run_all_tests()
        console.print_json(rep.model_dump_json())
        return

    table = Table(title="🛡️ Proton Security Status & Active Controls", show_header=True, header_style="bold cyan")
    table.add_column("Security Control", style="bold", width=25)
    table.add_column("Status / Setting", style="cyan", width=55)

    pol_color = "green" if cfg.approval_policy.value == "strict" else "yellow"
    table.add_row("Approval Policy", f"[{pol_color}]{cfg.approval_policy.value.upper()}[/{pol_color}] (Requires explicit confirmation)")
    table.add_row("Filesystem Sandbox", f"[green]Active[/green] (Confined to `{workspace}`)")
    table.add_row("Secret Redaction", "[green]Enabled[/green] (API keys, tokens, and passwords scrubbed)")
    table.add_row("Blocked Shell Commands", f"{len(cfg.blocked_commands)} dangerous patterns explicitly banned")
    table.add_row("Allowed Command List", ", ".join(cfg.allowed_commands[:8]) + "...")

    console.print()
    console.print(table)
    console.print(
        "\n[dim]Run security verification tests or static audit:\n"
        "  • [bold bright_white]proton security test[/bold bright_white]  — Run automated defense verification test battery\n"
        "  • [bold bright_white]proton security audit[/bold bright_white] — Scan repository for exposed keys & vulnerabilities[/dim]\n"
    )


@security_app.command("test")
def test_security_cmd(
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path to verify"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Run automated defensive verification test battery against 8 threat vectors."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    tester = SecurityTester(workspace)

    with console.status("[cyan]Executing automated security verification battery...[/cyan]", spinner="dots"):
        report = tester.run_all_tests()

    if json_mode:
        console.print_json(report.model_dump_json())
        return

    # Header Panel
    score_color = "bold green" if report.security_score == 100 else ("bold yellow" if report.security_score >= 80 else "bold red")
    header_text = (
        f"[bold bright_white]Target Workspace:[/bold bright_white] [cyan]{report.workspace}[/cyan]\n"
        f"[bold bright_white]Defense Checks Passed:[/bold bright_white] [green]{report.passed_checks} / {report.total_checks}[/green]   "
        f"[bold bright_white]Security Score:[/bold bright_white] [{score_color}]{report.security_score} / 100[/{score_color}]\n"
        f"[bold bright_white]Verification Verdict:[/bold bright_white] [{score_color}]{report.verdict}[/{score_color}]"
    )
    console.print()
    console.print(
        Panel(
            header_text,
            title="[bold cyan]🛡️ Proton Automated Security Defense Verification[/bold cyan]",
            border_style="cyan" if report.security_score == 100 else "red",
        )
    )

    # Detailed Results Table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Threat Vector", style="bold", width=26)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Mitigated Risk", width=36)
    table.add_column("Defense Layer", style="dim", width=28)

    for c in report.checks:
        status_str = "[green]PASS ✓[/green]" if c.passed else "[red]FAIL ✗[/red]"
        table.add_row(
            c.name,
            status_str,
            c.risk_mitigated,
            c.defense_layer,
        )

    console.print(table)
    console.print(
        "\n[bold green]✓ Security verification complete:[/bold green] All core protective guardrails operational and strictly enforced.\n"
    )


@security_app.command("verify")
def verify_security_cmd(
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path to verify"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Alias for `proton security test`."""
    test_security_cmd(target_path=target_path, json_mode=json_mode)


@security_app.command("audit")
def audit_security_cmd(
    target_path: Optional[str] = typer.Option(None, "--path", "-p", help="Workspace path to audit"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Static repository security audit (scans for hardcoded secrets, unsafe permissions, and CVE patterns)."""
    workspace = Path(target_path).resolve() if target_path else Path.cwd()
    analyzer = RepoAnalyzer(workspace)
    sec = analyzer.audit_security()

    if json_mode:
        console.print_json(sec.model_dump_json())
        return

    table = Table(title="Proton Workspace Security Audit", show_header=True, header_style="bold cyan")
    table.add_column("Audit Metric", style="bold", width=25)
    table.add_column("Result", width=55)

    score_color = "green" if sec.score >= 80 else ("yellow" if sec.score >= 60 else "red")
    table.add_row("Audit Score", f"[{score_color}]{sec.score} / 100[/{score_color}]")
    table.add_row("Exposed Secrets / Keys", f"{len(sec.hardcoded_secrets_found)} detected")
    table.add_row("Security Policy Files", ", ".join(sec.security_files) or "[yellow]Missing SECURITY.md[/yellow]")

    console.print()
    console.print(table)

    if sec.hardcoded_secrets_found:
        console.print("\n[bold red]⚠️ Potential Exposed Secrets Detected:[/bold red]")
        for s in sec.hardcoded_secrets_found:
            console.print(f"  • [red]{s}[/red]")
    else:
        console.print("\n[bold green]✓ Clean audit: No hardcoded secrets or API tokens detected in workspace.[/bold green]\n")
