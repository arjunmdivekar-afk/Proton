"""Interactive Terminal Web Browser with Search, Link Navigation, and AI Copilot."""

import asyncio
import os
import sys
import re
from typing import Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from proton import __version__
from proton.browser.engine import ProtonBrowserEngine, BrowserPage
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry


class ProtonBrowserApp:
    """Interactive Proton Browser application."""

    def __init__(self, ai_mode: bool = False, initial_target: Optional[str] = None) -> None:
        self.ai_mode = ai_mode
        self.initial_target = initial_target
        self.engine = ProtonBrowserEngine()
        self.console = Console(safe_box=True)
        try:
            self.session = PromptSession(history=InMemoryHistory())
        except Exception:
            self.session = None

        # Initialize AI infrastructure for AI Mode
        self.config_mgr = ConfigManager()
        self.conn_mgr = ConnectionManager(self.config_mgr)
        self.active_conn = self.conn_mgr.get_active_connection()
        self.provider = ProviderRegistry.get_provider_for_connection(self.active_conn)
        self.model_name = self.config_mgr.config.active_model or (
            self.active_conn.discovered_models[0].id if self.active_conn.discovered_models else "default"
        )

    def print_browser_header(self) -> None:
        """Render browser address bar and navigation status."""
        curr = self.engine.current_page
        url_display = curr.url if curr else "about:blank"
        title_display = curr.title if curr else "New Tab"

        ai_badge = "[bold green]● AI Copilot Active[/bold green]" if self.ai_mode else "[dim]○ Standard Mode[/dim]"
        nav_info = f"Back: {'✓' if self.engine.can_go_back else '✗'} | Fwd: {'✓' if self.engine.can_go_forward else '✗'}"

        header = (
            f"[bold cyan]PROTON BROWSER[/bold cyan] [dim]v{__version__}[/dim]  {ai_badge}\n"
            f"[bold]Title:[/bold] [bright_white]{title_display}[/bright_white]\n"
            f"[bold]URL:[/bold] [cyan]{url_display}[/cyan]  [dim]({nav_info})[/dim]"
        )
        self.console.print(Panel(header, style="cyan", border_style="cyan"))

    def render_page(self, page: BrowserPage) -> None:
        """Render page content and link references."""
        self.console.print()
        if page.error:
            self.console.print(f"[bold red]Navigation Error:[/bold red] {page.error}")
            return

        # Render Markdown / Clean Text Content with safe fallback
        try:
            self.console.print(Markdown(page.content))
        except Exception:
            self.console.print(page.content)

        # Show interactive quick links prompt
        if page.links:
            self.console.print(
                f"\n[dim]----------------------------------------------------------------------------------------[/dim]\n"
                f"[bold cyan]Interactive Links ({len(page.links)} found):[/bold cyan] "
                f"[dim]Type [1-{min(len(page.links), 15)}] to open a link, `links` to list all, `search <q>` to search, or `help`.[/dim]"
            )
            # Show preview of first 6 links if not on search results
            if not page.is_search:
                for l in page.links[:6]:
                    self.console.print(f"  [bold cyan][{l.index}][/bold cyan] {l.text} [dim]-> {l.url[:60]}[/dim]")
                if len(page.links) > 6:
                    self.console.print(f"  [dim]... and {len(page.links) - 6} more links. Type `links` to view all.[/dim]")

    def show_links_table(self) -> None:
        """Display full table of interactive links for the current page."""
        page = self.engine.current_page
        if not page or not page.links:
            self.console.print("[yellow]No links found on this page.[/yellow]")
            return

        table = Table(title=f"Links on: {page.title}", show_header=True, header_style="bold cyan")
        table.add_column("#", style="bold cyan", width=4)
        table.add_column("Link Text", style="bold")
        table.add_column("Destination URL", style="dim")

        for l in page.links:
            table.add_row(str(l.index), l.text[:50], l.url[:70])

        self.console.print(table)
        self.console.print("[dim]Type a link number to navigate (e.g. `1` or `open 1`).[/dim]")

    async def summarize_page_with_ai(self) -> None:
        """Use AI to summarize the active page."""
        page = self.engine.current_page
        if not page or not page.content.strip():
            self.console.print("[yellow]No page content to summarize. Navigate to a page first.[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Proton AI is analyzing and summarizing: {page.title}...[/bold cyan]\n")
        prompt = (
            f"Please read this web page from {page.url} (Title: {page.title}) and provide a concise, structured executive summary with key points and takeaways:\n\n"
            f"{page.content[:6000]}"
        )
        await self._ask_ai(prompt)

    async def ask_page_with_ai(self, question: str) -> None:
        """Answer questions about the active page using AI."""
        page = self.engine.current_page
        if not page or not page.content.strip():
            self.console.print("[yellow]No page loaded. Please search or open a URL first.[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Proton AI answering about {page.title}...[/bold cyan]\n")
        prompt = (
            f"You are reviewing the following web page from {page.url}:\n\n"
            f"--- PAGE CONTENT ---\n{page.content[:6000]}\n--- END CONTENT ---\n\n"
            f"Question from user: {question}\n\n"
            f"Please answer accurately based on the page content with clear explanations."
        )
        await self._ask_ai(prompt)

    async def _ask_ai(self, prompt: str) -> None:
        """Stream an AI answer directly inside the browser."""
        from proton.core.types import Message, Role
        messages = [
            Message(
                role=Role.SYSTEM,
                content="You are Proton, the embedded AI Co-Pilot in Proton Browser. Answer accurately based on the browsing context."
            ),
            Message(role=Role.USER, content=prompt),
        ]

        status = self.console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots")
        status.start()
        try:
            async for chunk in self.provider.stream_chat(messages=messages, model=self.model_name):
                if status is not None:
                    status.stop()
                    status = None

                if chunk.delta:
                    self.console.print(chunk.delta, end="", highlight=False)
            self.console.print("\n")
        except Exception as e:
            if status is not None:
                status.stop()
            self.console.print(f"\n[red]AI Error: {e}[/red]\n")

    def show_help(self) -> None:
        """Display browser commands and help table."""
        table = Table(title="Proton Browser Controls", show_header=True, header_style="bold cyan")
        table.add_column("Command / Action", style="bold")
        table.add_column("Description")
        table.add_row("[1-99]", "Navigate directly to numbered link on current page (e.g. `1` or `open 1`)")
        table.add_row("search <query>", "Search the web via DuckDuckGo (e.g. `search python fastapi`)")
        table.add_row("open <url>", "Open a web URL directly (e.g. `open react.dev` or `open https://python.org`)")
        table.add_row("links", "Show a numbered table of all interactive hyperlinks on this page")
        table.add_row("back / b", "Go back to the previous page in history")
        table.add_row("forward / f", "Go forward in history")
        table.add_row("reload / r", "Reload current page")
        table.add_row("ai / ai on / ai off", "Toggle AI Copilot mode")
        table.add_row("summarize / sum", "AI page summarizer (generates structured overview of current page)")
        table.add_row("ask <question>", "Ask the AI Copilot questions about the active web page")
        table.add_row("help", "Show this help menu")
        table.add_row("exit / quit / q", "Exit Proton Browser")
        self.console.print(table)

    async def run(self) -> None:
        """Main interactive browser REPL loop."""
        os.system("cls" if sys.platform == "win32" else "clear")
        self.print_browser_header()

        # Load initial target if specified
        if self.initial_target:
            self.console.print(f"\n[cyan]Loading: {self.initial_target}...[/cyan]")
            page = await self.engine.navigate(self.initial_target)
            self.render_page(page)
        else:
            # Default welcome search page
            welcome_content = (
                "# Welcome to Proton Browser\n\n"
                "A fast, keyboard-first, AI-assisted web browser operating directly in your terminal.\n\n"
                "### Quick Start:\n"
                "- Type any search query (e.g. `react 19 release notes` or `python documentation`)\n"
                "- Type any website URL (e.g. `https://react.dev` or `github.com`)\n"
                "- Type `help` to view all navigation keys and AI commands.\n"
            )
            welcome_page = BrowserPage(url="about:home", title="Proton Home", content=welcome_content)
            self.engine._push_page(welcome_page)
            self.render_page(welcome_page)

        while True:
            curr = self.engine.current_page
            from urllib.parse import urlparse
            domain_label = urlparse(curr.url).netloc if curr and curr.url.startswith("http") else "proton"
            prompt_text = HTML(f"<ansicyan><b>proton-browser</b></ansicyan> [<b>{domain_label}</b>] &gt; ")

            try:
                if self.session is not None:
                    user_input = await self.session.prompt_async(prompt_text)
                else:
                    user_input = input(f"proton-browser [{domain_label}] > ")
            except (KeyboardInterrupt, EOFError):
                break

            cmd = user_input.strip()
            if not cmd:
                continue

            # Check for link number directly (e.g. `1`, `[1]`, `open 1`, `goto 1`, `click 1`)
            link_match = re.match(r"^(?:open\s+|goto\s+|link\s+|click\s+)?\[?(\d+)\]?$", cmd, re.IGNORECASE)
            if link_match:
                link_num = int(link_match.group(1))
                self.console.print(f"\n[cyan]Navigating to Link [{link_num}]...[/cyan]")
                page = await self.engine.open_link_by_index(link_num)
                if page:
                    os.system("cls" if sys.platform == "win32" else "clear")
                    self.print_browser_header()
                    self.render_page(page)
                else:
                    self.console.print(f"[yellow]Link [{link_num}] not found on this page. Type `links` to view available links.[/yellow]")
                continue

            lower_cmd = cmd.lower()

            if lower_cmd in ("exit", "quit", "q"):
                self.console.print("[dim]Exiting Proton Browser. Goodbye![/dim]")
                break

            elif lower_cmd == "help":
                self.show_help()

            elif lower_cmd in ("back", "b"):
                page = self.engine.go_back()
                if page:
                    os.system("cls" if sys.platform == "win32" else "clear")
                    self.print_browser_header()
                    self.render_page(page)
                else:
                    self.console.print("[yellow]No previous page in history.[/yellow]")

            elif lower_cmd in ("forward", "f"):
                page = self.engine.go_forward()
                if page:
                    os.system("cls" if sys.platform == "win32" else "clear")
                    self.print_browser_header()
                    self.render_page(page)
                else:
                    self.console.print("[yellow]No forward page in history.[/yellow]")

            elif lower_cmd in ("reload", "r"):
                if self.engine.current_page:
                    os.system("cls" if sys.platform == "win32" else "clear")
                    self.print_browser_header()
                    page = await self.engine.navigate(self.engine.current_page.url)
                    self.render_page(page)

            elif lower_cmd == "links":
                self.show_links_table()

            elif lower_cmd in ("ai", "ai on"):
                self.ai_mode = True
                self.console.print("[bold green]✓ AI Copilot Mode Enabled.[/bold green] Ask questions with `ask <question>` or `summarize`.")

            elif lower_cmd == "ai off":
                self.ai_mode = False
                self.console.print("[yellow]○ AI Copilot Mode Disabled.[/yellow]")

            elif lower_cmd in ("summarize", "sum", "summary"):
                await self.summarize_page_with_ai()

            elif lower_cmd.startswith("ask "):
                question = cmd[4:].strip()
                await self.ask_page_with_ai(question)

            elif lower_cmd.startswith("open "):
                target_url = cmd[5:].strip()
                self.console.print(f"\n[cyan]Opening: {target_url}...[/cyan]")
                page = await self.engine.navigate(target_url)
                os.system("cls" if sys.platform == "win32" else "clear")
                self.print_browser_header()
                self.render_page(page)

            elif lower_cmd.startswith("search "):
                q = cmd[7:].strip()
                self.console.print(f"\n[cyan]Searching DuckDuckGo for: {q}...[/cyan]")
                page = await self.engine.search(q)
                os.system("cls" if sys.platform == "win32" else "clear")
                self.print_browser_header()
                self.render_page(page)

            else:
                # If in AI mode and not a navigation command, answer with AI context
                if self.ai_mode and not re.match(r"^(https?://|[a-zA-Z0-9_\-]+\.[a-zA-Z]{2,})", cmd):
                    await self.ask_page_with_ai(cmd)
                else:
                    # General input: treat as URL or search query
                    self.console.print(f"\n[cyan]Loading: {cmd}...[/cyan]")
                    page = await self.engine.navigate(cmd)
                    os.system("cls" if sys.platform == "win32" else "clear")
                    self.print_browser_header()
                    self.render_page(page)
