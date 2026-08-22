"""Interactive Stream-First REPL for Proton."""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table

from proton import __version__
from proton.core.types import Message, Role
from proton.core.config import ConfigManager, get_proton_home
from proton.connection.manager import ConnectionManager
from proton.connection.wizard import run_connection_wizard
from proton.providers.registry import ProviderRegistry
from proton.security.sandbox import FilesystemSandbox
from proton.security.policy import PolicyEngine
from proton.security.approval import ApprovalManager
from proton.tools.registry import ToolRegistry
from proton.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, SearchCodeTool
from proton.tools.shell import ShellExecuteTool
from proton.tools.git import GitStatusTool, GitDiffTool, GitLogTool, GitCommitTool
from proton.tools.coding import ApplyPatchTool, RunTestsTool
from proton.tools.rag_tools import RAGSearchTool, RAGIndexTool
from proton.tools.memory_tools import MemoryAddTool, MemorySearchTool
from proton.rag.pipeline import RAGPipeline
from proton.memory.manager import memory_manager
from proton.sessions.manager import SessionManager
from proton.agent.context import ContextAssembler
from proton.agent.engine import AgentEngine
from proton.tools.web_search import DuckDuckGoSearchTool, FetchWebPageTool, search_duckduckgo_async
from proton.tui.autocomplete import SlashCommandCompleter
from proton.tui.code_highlighter import StreamingCodeHighlighter
class KeyInterruptListener:
    """Non-blocking background listener for cancellation hotkeys (Ctrl+T or Ctrl+C)."""

    def __init__(self) -> None:
        self.stop_requested = asyncio.Event()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass

    async def _listen_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while self._running:
            if sys.platform == "win32":
                try:
                    pressed = await loop.run_in_executor(None, self._check_win32_key)
                    if pressed:
                        self.stop_requested.set()
                        break
                except Exception:
                    pass
            await asyncio.sleep(0.04)

    def _check_win32_key(self) -> bool:
        import msvcrt
        import time
        t_end = time.time() + 0.04
        while time.time() < t_end:
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    # b"\x14" is Ctrl+T (ASCII 20)
                    # b"\x03" is Ctrl+C (ASCII 3)
                    if ch in (b"\x14", b"\x03"):
                        return True
            except Exception:
                pass
            time.sleep(0.01)
        return False


class ProtonREPL:
    """Stream-First Terminal REPL for Proton."""

    def __init__(self, workspace_path: Optional[Path] = None, initial_session: Optional[str] = None) -> None:
        self.workspace_path = (workspace_path or Path.cwd()).resolve()
        self.console = Console()
        self.config_mgr = ConfigManager(self.workspace_path)
        self.conn_mgr = ConnectionManager(self.config_mgr)
        self.session_mgr = SessionManager()
        self.chat_only_mode = False

        # Initialize Security & Sandbox
        self.sandbox = FilesystemSandbox(self.workspace_path)
        self.policy_engine = PolicyEngine(self.config_mgr.config.security)
        self.approval_mgr = ApprovalManager(self.config_mgr.config.security.approval_policy)

        # Initialize Tools
        self.tool_registry = ToolRegistry(
            policy_engine=self.policy_engine,
            approval_manager=self.approval_mgr,
        )
        self._register_default_tools()

        # Active Session
        active_conn = self.conn_mgr.get_active_connection()
        if initial_session:
            existing = self.session_mgr.find_session_by_name_or_id(initial_session)
            if existing:
                self.current_session = existing
            else:
                self.current_session = self.session_mgr.create_session(
                    workspace_path=str(self.workspace_path),
                    title=initial_session.lstrip("-"),
                    connection_id=active_conn.id,
                    model_id=self.config_mgr.config.active_model,
                )
        else:
            self.current_session = self.session_mgr.create_session(
                workspace_path=str(self.workspace_path),
                connection_id=active_conn.id,
                model_id=self.config_mgr.config.active_model,
            )

        # Setup prompt_toolkit history & keybindings
        from prompt_toolkit.key_binding import KeyBindings
        self.key_bindings = KeyBindings()

        @self.key_bindings.add("c-t")
        def _on_ctrl_t(event):
            event.app.exit(result="__CTRL_T_SAVE_EXIT__")

        hist_file = str(get_proton_home() / "history.txt")
        try:
            self.prompt_session = PromptSession(
                history=FileHistory(hist_file),
                completer=SlashCommandCompleter(),
                key_bindings=self.key_bindings,
            )
        except Exception:
            from prompt_toolkit.input import DummyInput
            from prompt_toolkit.output import DummyOutput

            self.prompt_session = PromptSession(
                history=FileHistory(hist_file),
                completer=SlashCommandCompleter(),
                key_bindings=self.key_bindings,
                input=DummyInput(),
                output=DummyOutput(),
            )

    def _register_default_tools(self) -> None:
        sb = self.sandbox
        self.tool_registry.register(ReadFileTool(sb))
        self.tool_registry.register(WriteFileTool(sb))
        self.tool_registry.register(EditFileTool(sb))
        self.tool_registry.register(ListDirectoryTool(sb))
        self.tool_registry.register(SearchCodeTool(sb))
        self.tool_registry.register(ShellExecuteTool(sb))
        self.tool_registry.register(GitStatusTool(sb))
        self.tool_registry.register(GitDiffTool(sb))
        self.tool_registry.register(GitLogTool(sb))
        self.tool_registry.register(GitCommitTool(sb))
        self.tool_registry.register(ApplyPatchTool(sb))
        self.tool_registry.register(RunTestsTool(sb))

        # RAG pipeline & tools
        active_conn = self.conn_mgr.get_active_connection()
        provider = ProviderRegistry.get_provider_for_connection(active_conn)
        self.rag_pipeline = RAGPipeline(
            workspace_root=self.workspace_path,
            provider=provider,
            config=self.config_mgr.config.rag,
        )
        self.tool_registry.register(RAGSearchTool(self.rag_pipeline))
        self.tool_registry.register(RAGIndexTool(self.rag_pipeline))
        self.tool_registry.register(MemoryAddTool(memory_manager))
        self.tool_registry.register(MemorySearchTool(memory_manager))

        # Web search tools (DuckDuckGo live lookup)
        self.tool_registry.register(DuckDuckGoSearchTool())
        self.tool_registry.register(FetchWebPageTool())

    def print_banner(self) -> None:
        active_conn = self.conn_mgr.get_active_connection()
        active_model = self.config_mgr.config.active_model or "auto"
        status_color = "green" if active_conn.is_local else "yellow"

        banner = Panel.fit(
            f"[bold cyan]PROTON AI ASSISTANT[/bold cyan] [dim]v{__version__}[/dim]\n"
            f"[bold]Provider:[/bold] [cyan]{active_conn.provider.value}[/cyan]  "
            f"[bold]Connection:[/bold] [{status_color}]{active_conn.name} ({active_conn.base_url})[/{status_color}]\n"
            f"[bold]Model:[/bold] [magenta]{active_model}[/magenta]  "
            f"[bold]Workspace:[/bold] [dim]{self.workspace_path.name}[/dim]  "
            f"[bold]Security:[/bold] [yellow]Strict Approval[/yellow]\n\n"
            f"[dim]Type your request or use slash commands like [bold]/help[/bold], [bold]/connection[/bold], [bold]/model[/bold], [bold]/mode[/bold], [bold]/exit[/bold][/dim]\n"
            f"[dim]Tip: Press [bold cyan]Ctrl+T[/bold cyan] anytime to end and name/save your conversation session.[/dim]",
            border_style="cyan",
        )
        self.console.print(banner)

        if self.current_session and getattr(self.current_session, "messages", None) and len(self.current_session.messages) > 0:
            self.console.print(
                f"[bold green]● Resumed Conversation Session:[/bold green] [bold cyan]{self.current_session.title}[/bold cyan] "
                f"[dim]({len(self.current_session.messages)} messages loaded)[/dim]\n"
            )
            highlighter = StreamingCodeHighlighter(self.console)
            for msg in self.current_session.messages:
                if msg.role.value == "user":
                    self.console.print(f"[bold cyan]User:[/bold cyan] {msg.content.strip()}\n")
                elif msg.role.value == "assistant":
                    self.console.print(f"[bold magenta]Proton:[/bold magenta]")
                    highlighter.reset()
                    highlighter.process_chunk(msg.content.strip())
                    highlighter.flush()
                    self.console.print("\n")
                elif msg.role.value == "tool":
                    if msg.content:
                        self.console.print(f"[dim]Tool Result: {msg.content.strip()}[/dim]\n")

    def _prompt_and_save_session(self) -> None:
        """Prompt user to name and save conversation session upon exit/Ctrl+T."""
        try:
            self.console.print("\n[bold cyan]💾 Save Conversation Session[/bold cyan]")
            self.console.print("[dim]Name this conversation to resume it later (e.g. 'test' -> `proton --test`), or press Enter to skip:[/dim]")
            name = input("Session name: ").strip()
            if name:
                clean_name = name.lstrip("-").strip()
                self.session_mgr.rename_session(self.current_session.id, clean_name)
                self.current_session.title = clean_name
                self.console.print(
                    Panel.fit(
                        f"[bold green]✓ Conversation saved as:[/bold green] [bold cyan]{clean_name}[/bold cyan]\n"
                        f"[dim]You can resume this conversation anytime using:[/dim]\n"
                        f"  [bold bright_white]proton --{clean_name}[/bold bright_white]\n"
                        f"  [dim]or[/dim] [bold bright_white]proton --session {clean_name}[/bold bright_white]",
                        border_style="green",
                    )
                )
        except Exception:
            pass
        self.console.print("[yellow]Exiting Proton... Goodbye![/yellow]")

    async def run(self) -> None:
        self.print_banner()

        while True:
            try:
                # Prompt loop in executor
                loop = asyncio.get_running_loop()
                user_input = await loop.run_in_executor(
                    None,
                    lambda: self.prompt_session.prompt(HTML("<ansicyan><b>proton &gt; </b></ansicyan>")).strip()
                )

                if user_input == "__CTRL_T_SAVE_EXIT__":
                    self._prompt_and_save_session()
                    break

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    handled = await self._handle_slash_command(user_input)
                    if handled == "exit":
                        break
                    continue

                # Normal Agent prompt execution
                await self._execute_agent_turn(user_input)

            except (KeyboardInterrupt, EOFError):
                self._prompt_and_save_session()
                break
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")

    async def _handle_slash_command(self, cmd: str) -> Optional[str]:
        parts = cmd.split(maxsplit=1)
        base = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if base in ("/exit", "/quit", "/q"):
            self._prompt_and_save_session()
            return "exit"

        elif base == "/clear":
            os.system("cls" if sys.platform == "win32" else "clear")
            self.print_banner()

        elif base == "/help":
            table = Table(title="Proton Slash Commands", show_header=True, header_style="bold cyan")
            table.add_column("Command", style="bold")
            table.add_row("/browser", "Launch Proton Browser with search and links (/browser [--ai_mode])")
            table.add_row("/web-search", "Search the web via DuckDuckGo and summarize with AI (/web-search <query>)")
            table.add_row("/connection", "Configure LM Studio, Ollama, IP address, Port, test connection")
            table.add_row("/model", "List discovered models or switch active model")
            table.add_row("/mode", "Switch mode (/mode chat or /mode agent)")
            table.add_row("/rag", "Manage RAG vector index (/rag index, /rag search <q>)")
            table.add_row("/memory", "Search or list persistent project rules")
            table.add_row("/review", "Review unstaged git diff and changes")
            table.add_row("/diff", "View unified git diff")
            table.add_row("/status", "Show git status and active session info")
            table.add_row("/doctor", "Run diagnostic environment and connection health checks")
            table.add_row("/export", "Export conversation to markdown")
            table.add_row("/clear", "Clear terminal screen")
            table.add_row("/exit", "Exit Proton")
            self.console.print(table)

        elif base == "/connection":
            await run_connection_wizard(self.conn_mgr)

        elif base == "/mode":
            mode_arg = arg.strip().lower()
            if mode_arg in ("chat", "conversational", "talk"):
                self.chat_only_mode = True
                self.console.print("[bold green]✓ Switched to Pure Chat Mode (Tools disabled).[/bold green]")
            elif mode_arg in ("agent", "tools", "auto"):
                self.chat_only_mode = False
                self.console.print("[bold green]✓ Switched to Agent Mode (Tools enabled).[/bold green]")
            else:
                current = "Pure Chat (Tools disabled)" if self.chat_only_mode else "Agent Mode (Tools enabled)"
                self.console.print(f"[bold]Current Mode:[/bold] {current}")
                self.console.print("[dim]Usage: `/mode chat` (pure text chat) or `/mode agent` (coding agent with tools)[/dim]")

        elif base == "/model":
            active_conn = self.conn_mgr.get_active_connection()
            if arg:
                self.config_mgr.set_active_model(arg)
                self.console.print(f"[bold green]Active model switched to:[/bold green] {arg}")
            else:
                self.console.print(f"[bold]Active Connection:[/bold] {active_conn.name} ({active_conn.base_url})")
                self.console.print(f"[bold]Active Model:[/bold] {self.config_mgr.config.active_model or 'auto'}")
                if active_conn.discovered_models:
                    self.console.print("\n[bold]Discovered Models on this server:[/bold]")
                    for m in active_conn.discovered_models:
                        self.console.print(f"  • [cyan]{m.id}[/cyan]")
                else:
                    self.console.print("[dim]No models discovered yet. Run `/connection` -> Test Connection to discover.[/dim]")

        elif base == "/diff":
            git_diff_tool = self.tool_registry.get_tool("git_diff")
            if git_diff_tool:
                res = await git_diff_tool.run()
                render_diff(res.get("diff", ""))

        elif base == "/review":
            self.console.print("[cyan]Analyzing git diff for code review...[/cyan]")
            git_diff_tool = self.tool_registry.get_tool("git_diff")
            if git_diff_tool:
                res = await git_diff_tool.run()
                diff_content = res.get("diff", "")
                if not diff_content.strip():
                    self.console.print("[yellow]No git changes detected to review.[/yellow]")
                else:
                    prompt = f"Please review the following git diff for correctness, bugs, and security risks:\n\n```diff\n{diff_content}\n```"
                    await self._execute_agent_turn(prompt)

        elif base == "/rag":
            if arg.startswith("fetch"):
                self.console.print("[cyan]Fetching coding knowledge corpus...[/cyan]")
                from proton.rag.corpus_fetcher import fetch_and_build_knowledge_corpus
                saved = await fetch_and_build_knowledge_corpus()
                if saved:
                    self.console.print(f"[bold green]✓ Downloaded {len(saved)} programming knowledge guides.[/bold green]")
                    self.console.print("[cyan]Indexing knowledge corpus into vector store...[/cyan]")
                    stats = await self.rag_pipeline.index_directory(get_proton_home() / "knowledge")
                    self.console.print(f"[bold green]✓ Indexed {stats.files_indexed} files ({stats.chunks_created} chunks). Total chunks: {self.rag_pipeline.store.count()}[/bold green]")
                else:
                    self.console.print("[yellow]Could not download knowledge files.[/yellow]")
            elif arg.startswith("index"):
                self.console.print("[cyan]Indexing repository for RAG...[/cyan]")
                stats = await self.rag_pipeline.index_directory()
                self.console.print(f"[bold green]✓ Indexed {stats.files_indexed} files ({stats.chunks_created} chunks). Total chunks in DB: {self.rag_pipeline.store.count()}[/bold green]")
            elif arg.startswith("search"):
                q = arg[6:].strip()
                res = await self.rag_pipeline.search(q)
                self.console.print(f"[bold]Found {len(res)} results for '{q}':[/bold]")
                for r in res:
                    self.console.print(f"[cyan]{r.citation}[/cyan] [dim](score: {r.score:.3f})[/dim]\n{r.content[:200]}...\n")
            else:
                self.console.print(f"[bold]RAG Status:[/bold] Total indexed chunks: {self.rag_pipeline.store.count()}")
                self.console.print("[dim]Usage: `/rag fetch` (download coding knowledge), `/rag index`, or `/rag search <query>`[/dim]")

        elif base in ("/task", "/tasks"):
            subcmd = arg.strip().split(maxsplit=1)
            action = subcmd[0].lower() if subcmd else "list"
            sub_arg = subcmd[1] if len(subcmd) > 1 else ""

            from proton.tasks.manager import TaskManager
            from proton.tasks.runner import TaskRunner
            mgr = TaskManager()

            if action == "create":
                if not sub_arg:
                    self.console.print("[dim]Usage: `/task create \"<title>\" \"<goal>\"`[/dim]")
                else:
                    import shlex
                    try:
                        parts = shlex.split(sub_arg)
                    except Exception:
                        parts = [sub_arg]
                    title = parts[0] if parts else "Untitled Task"
                    goal = parts[1] if len(parts) > 1 else title
                    t = mgr.create_task(goal=goal, title=title, workspace_path=self.workspace_path)
                    self.console.print(f"[bold green]✓ Created task:[/bold green] [cyan]{t.id}[/cyan] — [bold]{t.title}[/bold] (Goal: {t.goal})")
            elif action in ("list", "ls", ""):
                tasks = mgr.list_tasks()
                if not tasks:
                    self.console.print("[dim]No persistent tasks recorded. Create one with `/task create <goal>`[/dim]")
                else:
                    self.console.print("[bold cyan]Persistent Tasks:[/bold cyan]")
                    for t in tasks:
                        self.console.print(f"  • [cyan]{t.id}[/cyan] [{t.status.value}] ({t.progress_pct}%) - {t.title}")
            elif action in ("show", "get", "info"):
                if not sub_arg:
                    self.console.print("[dim]Usage: `/task show <id>`[/dim]")
                else:
                    from proton.cli.task_cmd import show_task_cmd
                    show_task_cmd(sub_arg)
            elif action in ("run", "exec", "start"):
                if not sub_arg:
                    self.console.print("[dim]Usage: `/task run <id>`[/dim]")
                else:
                    runner = TaskRunner(mgr)
                    await runner.run_task(sub_arg)
                    self.print_banner()
            elif action == "pause":
                mgr.pause_task(sub_arg)
                self.console.print(f"[yellow]⏸ Paused task '{sub_arg}'.[/yellow]")
            elif action == "cancel":
                mgr.cancel_task(sub_arg)
                self.console.print(f"[red]✗ Cancelled task '{sub_arg}'.[/red]")
            else:
                self.console.print("[dim]Usage: `/task [create <goal> | list | show <id> | run <id> | pause <id> | cancel <id>]`[/dim]")

        elif base == "/agent":
            goal = arg.strip()
            if not goal:
                self.console.print("[dim]Usage: `/agent <goal>` (e.g. `/agent build a responsive landing page and run tests`)[/dim]")
            else:
                from proton.agent.max_agent import ProtonMaxAgent
                agent = ProtonMaxAgent(workspace_path=self.workspace_path)
                await agent.run(goal)
                self.print_banner()

        elif base in ("/stock", "/stocks"):
            sym = arg.strip() if arg.strip() else None
            from proton.stocks.app import ProtonStockApp
            stock_app = ProtonStockApp(initial_symbol=sym)
            await stock_app.run()
            self.print_banner()

        elif base in ("/browser", "/browse"):
            target = arg.strip()
            ai_flag = False
            if "--ai_mode" in target or "--ai" in target or "-a" in target:
                ai_flag = True
                target = target.replace("--ai_mode", "").replace("--ai", "").replace("-a", "").strip()

            from proton.browser.app import ProtonBrowserApp
            browser_app = ProtonBrowserApp(ai_mode=ai_flag, initial_target=target if target else None)
            await browser_app.run()
            self.print_banner()

        elif base in ("/web-search", "/search", "/web"):
            query = arg.strip()
            if not query:
                self.console.print("[bold cyan]DuckDuckGo Web Search is active.[/bold cyan]")
                self.console.print("[dim]Usage: `/web-search <query>` (e.g. `/web-search latest react 19 features`)[/dim]")
                self.console.print("[dim]Or ask naturally in prompt: 'search web for ...'[/dim]")
            else:
                self.console.print(f"\n[cyan]Searching DuckDuckGo for:[/cyan] [bold]{query}[/bold]...")
                search_status = self.console.status("[bold cyan]Querying DuckDuckGo...[/bold cyan]", spinner="dots")
                search_status.start()
                try:
                    results = await search_duckduckgo_async(query, max_results=5)
                finally:
                    search_status.stop()

                if not results or (len(results) == 1 and "Search Error" in results[0].get("title", "")):
                    self.console.print("[yellow]No web search results found for this query.[/yellow]")
                else:
                    # Display search results summary table
                    table = Table(title=f"DuckDuckGo Results for: {query}", show_header=True, header_style="bold cyan")
                    table.add_column("#", style="dim", width=3)
                    table.add_column("Title", style="bold")
                    table.add_column("URL", style="dim cyan")

                    for idx, r in enumerate(results, 1):
                        table.add_row(str(idx), r.get("title", "Untitled"), r.get("url", ""))
                    self.console.print(table)

                    # Pass search results to AI to synthesize and answer with citations
                    context_blocks = []
                    for idx, r in enumerate(results, 1):
                        context_blocks.append(
                            f"[{idx}] {r.get('title')}\nURL: {r.get('url')}\nSnippet: {r.get('snippet')}"
                        )
                    search_context = "\n\n".join(context_blocks)

                    ai_prompt = (
                        f"I searched DuckDuckGo for: \"{query}\".\n"
                        f"Here are the live web search results:\n\n{search_context}\n\n"
                        f"Please synthesize these results and provide a comprehensive, accurate answer to \"{query}\" with citations."
                    )
                    await self._execute_agent_turn(ai_prompt)

        elif base == "/memory":
            import shlex
            parts = shlex.split(arg) if arg else []
            sub = parts[0].lower() if parts else "list"

            from proton.memory.store import MemoryType
            from proton.cli.memory_cmd import list_memories_cmd, add_memory_cmd, search_memory_cmd, forget_memory_cmd, clear_memory_cmd, export_memory_cmd

            if sub == "list":
                m_type = parts[1] if len(parts) > 1 else None
                list_memories_cmd(mem_type=m_type)
            elif sub == "add":
                if len(parts) < 2:
                    self.console.print("[dim]Usage: `/memory add \"<content>\" [CATEGORY]` or `/memory add [CATEGORY] \"<content>\"`[/dim]")
                else:
                    # Check if first or second arg is category
                    first, second = parts[1], (parts[2] if len(parts) > 2 else None)
                    cat = "PROJECT"
                    content = first
                    if first.upper() in [m.value for m in MemoryType]:
                        cat = first.upper()
                        content = second or ""
                    elif second and second.upper() in [m.value for m in MemoryType]:
                        cat = second.upper()
                    add_memory_cmd(content=content, mem_type=cat)
            elif sub == "search":
                q = " ".join(parts[1:]) if len(parts) > 1 else ""
                if not q:
                    self.console.print("[dim]Usage: `/memory search \"<query>\"`[/dim]")
                else:
                    search_memory_cmd(query=q)
            elif sub in ("forget", "delete", "rm"):
                if len(parts) < 2 or not parts[1].isdigit():
                    self.console.print("[dim]Usage: `/memory forget <id>`[/dim]")
                else:
                    forget_memory_cmd(record_id=int(parts[1]))
            elif sub == "export":
                export_memory_cmd()
            elif sub == "clear":
                cat = parts[1] if len(parts) > 1 else None
                clear_memory_cmd(mem_type=cat, yes=True)
            else:
                # If user typed arbitrary search string directly
                search_memory_cmd(query=arg)

        elif base == "/inspect":
            sub = arg.strip().lower()
            from proton.inspect.analyzer import RepoAnalyzer
            analyzer = RepoAnalyzer(self.workspace_path)

            if sub == "security":
                from proton.cli.inspect_cmd import inspect_security_cmd
                inspect_security_cmd(str(self.workspace_path))
            elif sub == "architecture":
                from proton.cli.inspect_cmd import inspect_architecture_cmd
                inspect_architecture_cmd(str(self.workspace_path))
            elif sub == "dependencies":
                from proton.cli.inspect_cmd import inspect_dependencies_cmd
                inspect_dependencies_cmd(str(self.workspace_path))
            elif sub == "tests":
                from proton.cli.inspect_cmd import inspect_tests_cmd
                inspect_tests_cmd(str(self.workspace_path))
            elif sub == "performance":
                from proton.cli.inspect_cmd import inspect_performance_cmd
                inspect_performance_cmd(str(self.workspace_path))
            else:
                from proton.cli.inspect_cmd import default_inspect_callback
                import typer
                ctx = typer.Context(typer.main.get_command(inspect_app))
                default_inspect_callback(ctx, str(self.workspace_path), json_mode=False)

        elif base in ("/graph", "/knowledge-graph"):
            parts = arg.strip().split(maxsplit=1)
            sub = parts[0].lower() if parts else "stats"
            target_symbol = parts[1] if len(parts) > 1 else ""

            from proton.graph.engine import ProjectGraphEngine
            engine = ProjectGraphEngine(self.workspace_path)

            if sub in ("build", "index", "rebuild"):
                from proton.cli.graph_cmd import build_graph_cmd
                build_graph_cmd(str(self.workspace_path))
            elif sub in ("impact", "break", "whatif"):
                if not target_symbol:
                    self.console.print("[dim]Usage: `/graph impact <function_or_class>`[/dim]")
                else:
                    from proton.cli.graph_cmd import impact_graph_cmd
                    impact_graph_cmd(target_symbol, str(self.workspace_path))
            elif sub == "callers":
                if not target_symbol:
                    self.console.print("[dim]Usage: `/graph callers <function_or_class>`[/dim]")
                else:
                    from proton.cli.graph_cmd import callers_graph_cmd
                    callers_graph_cmd(target_symbol, str(self.workspace_path))
            elif sub == "tests":
                if not target_symbol:
                    self.console.print("[dim]Usage: `/graph tests <function_or_class>`[/dim]")
                else:
                    from proton.cli.graph_cmd import tests_graph_cmd
                    tests_graph_cmd(target_symbol, str(self.workspace_path))
            else:
                from proton.cli.graph_cmd import default_graph_callback
                import typer
                ctx = typer.Context(typer.main.get_command(graph_app))
                default_graph_callback(ctx, str(self.workspace_path))

        elif base in ("/new", "/reset"):
            active_conn = self.conn_mgr.get_active_connection()
            self.current_session = self.session_mgr.create_session(
                workspace_path=str(self.workspace_path),
                connection_id=active_conn.id,
                model_id=self.config_mgr.config.active_model,
            )
            self.console.print("[bold green]✓ Started a new conversation session.[/bold green]")

        elif base == "/session":
            if arg in ("new", "reset", "clear"):
                active_conn = self.conn_mgr.get_active_connection()
                self.current_session = self.session_mgr.create_session(
                    workspace_path=str(self.workspace_path),
                    connection_id=active_conn.id,
                    model_id=self.config_mgr.config.active_model,
                )
                self.console.print("[bold green]✓ Started a new conversation session.[/bold green]")
            elif arg == "list":
                sessions = self.session_mgr.list_sessions()
                self.console.print("[bold]Recent Sessions:[/bold]")
                for s in sessions:
                    active_marker = " ★ (current)" if s.id == self.current_session.id else ""
                    self.console.print(f"  • [cyan]{s.id}[/cyan]{active_marker} - {s.title} [dim]({s.message_count} messages)[/dim]")
            else:
                self.console.print(f"[bold]Current Session ID:[/bold] `{self.current_session.id}`")
                self.console.print("[dim]Usage: `/session new` or `/session list`[/dim]")

        elif base == "/doctor":
            if arg.strip().lower() in ("--sys", "-s", "sys", "system"):
                from proton.cli.doctor_cmd import run_system_diagnostics
                await run_system_diagnostics()
            else:
                from proton.cli.doctor_cmd import run_doctor_checks
                await run_doctor_checks(self.workspace_path)

        elif base == "/export":
            md = self.session_mgr.export_markdown(self.current_session.id)
            export_file = self.workspace_path / f"proton_session_{self.current_session.id}.md"
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(md)
            self.console.print(f"[bold green]✓ Exported conversation to:[/bold green] {export_file.name}")

        else:
            self.console.print(f"[red]Unknown slash command '{base}'. Type `/help` for available commands.[/red]")

        return None

    async def _execute_agent_turn(self, user_prompt: str) -> None:
        active_conn = self.conn_mgr.get_active_connection()
        provider = ProviderRegistry.get_provider_for_connection(active_conn)
        self.rag_pipeline.set_provider(provider)

        context_assembler = ContextAssembler(
            workspace_root=self.workspace_path,
            memory_mgr=memory_manager,
            rag_pipeline=self.rag_pipeline,
        )

        model_name = self.config_mgr.config.active_model or (
            active_conn.discovered_models[0].id if active_conn.discovered_models else "default"
        )

        engine = AgentEngine(
            provider=provider,
            tool_registry=self.tool_registry,
            context_assembler=context_assembler,
            model_name=model_name,
            max_steps=self.config_mgr.config.agent.max_steps,
        )

        # Load session history
        history_session = self.session_mgr.get_session(self.current_session.id)
        history_msgs = history_session.messages if history_session else []

        # Save user message to session
        self.session_mgr.append_message(
            self.current_session.id,
            Message(role=Role.USER, content=user_prompt),
        )

        listener = KeyInterruptListener()
        await listener.start()

        t_start = time.perf_counter()
        full_reply = ""
        self.console.print()
        highlighter = StreamingCodeHighlighter(self.console)

        # Animated spinning thinking bar while model evaluates prompt
        status = self.console.status(
            f"[bold cyan]Thinking...[/bold cyan] [dim]({model_name})[/dim]",
            spinner="dots",
        )
        status.start()

        try:
            async for chunk in engine.stream_run(
                user_input=user_prompt,
                history=history_msgs,
                session_id=self.current_session.id,
                use_rag=self.config_mgr.config.rag.enabled,
                disable_tools=self.chat_only_mode,
            ):
                if status is not None:
                    status.stop()
                    status = None

                if listener.stop_requested.is_set():
                    self.console.print("\n[bold yellow]■ Generation stopped (Ctrl+T).[/bold yellow]")
                    break

                if isinstance(chunk, str):
                    full_reply += chunk
                    highlighter.process_chunk(chunk)
            highlighter.flush()
        except (KeyboardInterrupt, asyncio.CancelledError):
            if status is not None:
                status.stop()
                status = None
            highlighter.flush()
            self.console.print("\n[bold yellow]■ Generation stopped (Ctrl+T/Ctrl+C).[/bold yellow]")
        finally:
            if status is not None:
                status.stop()
                status = None
            await listener.stop()

        t_elapsed = max(0.01, time.perf_counter() - t_start)

        if full_reply.strip():
            self.session_mgr.append_message(
                self.current_session.id,
                Message(role=Role.ASSISTANT, content=full_reply),
            )

            # Token usage & performance metrics
            user_prompt_tokens = max(1, len(user_prompt.strip()) // 4)
            if engine.last_usage and isinstance(engine.last_usage.get("completion_tokens"), (int, float)):
                completion_tokens = int(engine.last_usage["completion_tokens"])
            else:
                completion_tokens = max(1, len(full_reply) // 4)

            if completion_tokens <= 0:
                completion_tokens = max(1, len(full_reply) // 4)

            turn_total = user_prompt_tokens + completion_tokens
            tokens_per_sec = completion_tokens / t_elapsed

            # Context window resolution
            context_limit = 32768
            if active_conn.discovered_models:
                for m in active_conn.discovered_models:
                    if m.id == model_name or m.name == model_name:
                        context_limit = m.context_window or 32768
                        break

            # Calculate total session tokens
            updated_session = self.session_mgr.get_session(self.current_session.id)
            all_msgs = updated_session.messages if updated_session else []
            total_context_used = sum(len(m.content) // 4 for m in all_msgs)
            context_pct = min(100.0, (total_context_used / context_limit) * 100)

            # Render visual context progress bar
            bar_width = 10
            filled_blocks = int(round((context_pct / 100.0) * bar_width))
            filled_blocks = max(0, min(bar_width, filled_blocks))
            if filled_blocks == 0 and total_context_used > 0:
                filled_blocks = 1
            unfilled_blocks = bar_width - filled_blocks

            if context_pct < 60:
                bar_color = "green"
            elif context_pct < 85:
                bar_color = "yellow"
            else:
                bar_color = "bold red"

            context_bar = f"[{bar_color}]{'#' * filled_blocks}[/{bar_color}][dim]{'-' * unfilled_blocks}[/dim]"

            self.console.print(
                f"\n[dim]----------------------------------------------------------------------------------------[/dim]\n"
                f"[dim]⚡[/dim] [bold cyan]{tokens_per_sec:.1f} tok/s[/bold cyan]  "
                f"[dim]|[/dim]  [bold]Turn:[/bold] [yellow]{turn_total:,} tokens[/yellow] [dim]({user_prompt_tokens:,} prompt, {completion_tokens:,} reply)[/dim]  "
                f"[dim]|[/dim]  [bold]Context:[/bold] [{context_bar}] [{bar_color}]{total_context_used:,} / {context_limit:,} tokens[/{bar_color}] [dim]({context_pct:.1f}%)[/dim]"
            )

        self.console.print("\n")
