"""Top-level CLI entrypoint for Proton."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

import proton
from proton.tui.repl import ProtonREPL

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from proton.cli.connection_cmd import conn_app
from proton.cli.doctor_cmd import run_doctor_checks
from proton.cli.rag_cmd import rag_app
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry
from proton.agent.context import ContextAssembler
from proton.agent.engine import AgentEngine
from proton.tools.registry import ToolRegistry
from proton.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, SearchCodeTool
from proton.tools.shell import ShellExecuteTool
from proton.tools.git import GitStatusTool, GitDiffTool, GitLogTool, GitCommitTool
from proton.security.sandbox import FilesystemSandbox
from proton.security.policy import PolicyEngine
from proton.security.approval import ApprovalManager
from proton.core.types import ApprovalPolicy, RiskLevel, ApprovalDecision

app = typer.Typer(
    name="proton",
    help="Proton — Enterprise AI CLI Assistant & Coding Agent Platform",
    no_args_is_help=False,
)
console = Console()

# Attach Subcommands
app.add_typer(conn_app, name="connection", help="Manage AI server connections (LM Studio / Ollama)")
app.add_typer(rag_app, name="rag", help="Manage RAG indexing and knowledge retrieval")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]Proton[/bold cyan] version [green]{proton.__version__}[/green]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show Proton version"
    ),
    stdin: bool = typer.Option(False, "--stdin", help="Read prompt/data from stdin"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Resume named conversation session"),
    resume: Optional[str] = typer.Option(None, "--resume", help="Alias for --session"),
) -> None:
    """Launch Proton interactive REPL or execute prompt non-interactively."""
    if ctx.invoked_subcommand is not None:
        return

    # Check if piped input was provided
    pipe_input = ""
    if not sys.stdin.isatty() or stdin:
        try:
            pipe_input = sys.stdin.read().strip()
        except Exception:
            pass

    if pipe_input:
        asyncio.run(_run_non_interactive(pipe_input, json_mode=json_mode))
    else:
        # Launch Interactive TUI REPL (with optional resumed session)
        target_session = session or resume
        repl = ProtonREPL(initial_session=target_session)
        asyncio.run(repl.run())


async def _run_non_interactive(user_prompt: str, json_mode: bool = False) -> None:
    """Headless agent execution with standard text or JSON output."""
    workspace = Path.cwd()
    config_mgr = ConfigManager(workspace)
    conn_mgr = ConnectionManager(config_mgr)
    active_conn = conn_mgr.get_active_connection()
    provider = ProviderRegistry.get_provider_for_connection(active_conn)

    sandbox = FilesystemSandbox(workspace)
    policy = PolicyEngine(config_mgr.config.security)
    # In non-interactive mode, auto-allow safe and report
    approval_mgr = ApprovalManager(ApprovalPolicy.BALANCED)
    approval_mgr.set_custom_handler(lambda tool, args, risk: ApprovalDecision.ALLOW_ONCE)

    tool_reg = ToolRegistry(policy_engine=policy, approval_manager=approval_mgr)
    tool_reg.register(ReadFileTool(sandbox))
    tool_reg.register(WriteFileTool(sandbox))
    tool_reg.register(EditFileTool(sandbox))
    tool_reg.register(ListDirectoryTool(sandbox))
    tool_reg.register(SearchCodeTool(sandbox))
    tool_reg.register(ShellExecuteTool(sandbox))
    tool_reg.register(GitStatusTool(sandbox))
    tool_reg.register(GitDiffTool(sandbox))
    tool_reg.register(GitLogTool(sandbox))
    tool_reg.register(GitCommitTool(sandbox))

    context_assembler = ContextAssembler(workspace_root=workspace)
    model_name = config_mgr.config.active_model or (
        active_conn.discovered_models[0].id if active_conn.discovered_models else "default"
    )

    engine = AgentEngine(
        provider=provider,
        tool_registry=tool_reg,
        context_assembler=context_assembler,
        model_name=model_name,
        max_steps=15,
    )

    full_output = ""
    from proton.tui.code_highlighter import StreamingCodeHighlighter
    highlighter = StreamingCodeHighlighter(console) if not json_mode else None

    try:
        async for chunk in engine.stream_run(user_input=user_prompt, use_rag=False):
            if isinstance(chunk, str):
                full_output += chunk
                if not json_mode and highlighter:
                    highlighter.process_chunk(chunk)

        if json_mode:
            res_obj = {
                "success": True,
                "provider": active_conn.provider.value,
                "connection": active_conn.base_url,
                "model": model_name,
                "response": full_output.strip(),
            }
            print(json.dumps(res_obj, indent=2))
        else:
            if highlighter:
                highlighter.flush()
            print()

    except Exception as e:
        if json_mode:
            print(json.dumps({"success": False, "error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")


@app.command("ask")
def ask_command(
    query: str = typer.Argument(..., help="Question or prompt to answer"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON only"),
) -> None:
    """Non-interactive query command (e.g. `proton ask 'explain this error' --json`)."""
    asyncio.run(_run_non_interactive(query, json_mode=json_mode))


from proton.cli.doctor_cmd import run_doctor_checks, run_system_diagnostics

@app.command("doctor")
def doctor_command(
    sys_mode: bool = typer.Option(
        False, "--sys", "-s", help="Show host machine system hardware, RAM, CPU, disk, and OS diagnostics instead of app status"
    ),
) -> None:
    """Run environment, storage, and AI provider health diagnostics (or use --sys for host hardware status)."""
    if sys_mode:
        asyncio.run(run_system_diagnostics())
    else:
        asyncio.run(run_doctor_checks())


@app.command("models")
def models_command() -> None:
    """List available and discovered models across connections."""
    mgr = ConnectionManager()
    all_models = mgr.get_all_models()
    active_conn = mgr.get_active_connection()

    console.print(f"[bold]Active Connection:[/bold] {active_conn.name} ({active_conn.base_url})")
    console.print(f"[bold]Active Model:[/bold] [cyan]{mgr.config_mgr.config.active_model or 'auto'}[/cyan]\n")

    if all_models:
        console.print("[bold]Discovered Models:[/bold]")
        for m in all_models:
            console.print(f"  • [cyan]{m.id}[/cyan] [dim](Provider: {m.provider})[/dim]")
    else:
        console.print("[dim]No models discovered yet. Run `proton connection test` to discover models from your server.[/dim]")


from proton.cli.browser_cmd import launch_browser
from proton.cli.stock_cmd import launch_stock_dashboard
from proton.cli.agent_cmd import launch_max_agent
from proton.cli.task_cmd import task_app
from proton.cli.inspect_cmd import inspect_app
from proton.cli.graph_cmd import graph_app
from proton.cli.memory_cmd import memory_app
from proton.cli.benchmark_cmd import benchmark_app
from proton.cli.security_cmd import security_app
from proton.cli.server_cmd import launch_server
from proton.cli.hub_cmd import hub_app

app.add_typer(hub_app, name="model-hub", help="Explore, inspect, install, and manage Hugging Face Transformers models")
app.add_typer(hub_app, name="modelhub", help="Alias for proton model-hub")
app.add_typer(hub_app, name="hub", help="Alias for proton model-hub")
app.add_typer(task_app, name="task", help="Manage persistent development tasks (create, list, show, run, pause, resume, cancel)")
app.add_typer(task_app, name="tasks", help="Alias for proton task")
app.add_typer(security_app, name="security", help="Security verification, automated defense testing, and workspace audit")
app.add_typer(memory_app, name="memory", help="Manage categorized memories (PROJECT, DECISION, PREFERENCE, FACT, TASK, USER, SESSION)")
app.add_typer(inspect_app, name="inspect", help="Deep codebase inspection (architecture, security, dependencies, tests, performance)")
app.add_typer(graph_app, name="graph", help="Project Knowledge Graph & GraphRAG (impact analysis, callers, tests, AST map)")
app.add_typer(benchmark_app, name="benchmark", help="Benchmark LLM models (latency, speed, context, tool calling, RAG, coding, planning, error recovery)")
app.command("server", help="Launch Proton Autonomous AI Server & REST/SSE API (http://127.0.0.1:8787)")(launch_server)
app.command("agent", help="Launch Proton Max-Level Autonomous Agent — 10-stage lifecycle with planning, tools, tests, self-healing, and audit reporting")(launch_max_agent)
app.command("browser", help="Launch Proton Browser — keyboard-first terminal web browser with DuckDuckGo search, link navigation, and AI mode")(launch_browser)
app.command("stock", help="Launch Proton Stock Tracker — Live stocks in Rupees (₹) with 10-minute auto-refresh, 20 stocks per page, and detailed charts")(launch_stock_dashboard)
app.command("stocks", help="Alias for proton stock")(launch_stock_dashboard)


def main() -> None:
    # Check if a dynamic named session flag like `proton --test` was passed directly
    args = sys.argv[1:]
    known_flags = {"--version", "-v", "--help", "-h", "--stdin", "--json", "--session", "-s", "--resume"}
    known_subcmds = {"server", "agent", "browser", "stock", "stocks", "task", "tasks", "security", "memory", "inspect", "graph", "benchmark", "connection", "rag", "ask", "doctor", "model-hub", "modelhub", "hub"}

    if args:
        first = args[0]
        if first.startswith("--") and first not in known_flags and not any(first.startswith(f"--{k}") for k in ("help", "version", "stdin", "json", "session", "resume")):
            session_name = first.lstrip("-")
            repl = ProtonREPL(initial_session=session_name)
            asyncio.run(repl.run())
            return

    app()


if __name__ == "__main__":
    main()
