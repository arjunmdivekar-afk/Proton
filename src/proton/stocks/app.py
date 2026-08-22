"""Interactive Terminal Stock Dashboard with Live 10-Second Refresh, Loading Spinner, and Detail Charts."""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import List, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton import __version__
from proton.stocks.service import StockDataService, StockQuote, StockDetail
from proton.stocks.chart import render_stock_chart
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry


class ProtonStockApp:
    """Live interactive stock market tracker and stock inspector."""

    def __init__(self, initial_symbol: Optional[str] = None, page: int = 1) -> None:
        self.service = StockDataService()
        self.current_page = max(1, min(self.service.get_total_pages(), page))
        self.initial_symbol = initial_symbol.upper() if initial_symbol else None
        self.console = Console(safe_box=True)
        try:
            self.session = PromptSession(history=InMemoryHistory())
        except Exception:
            self.session = None

        # AI connection for AI Stock Analysis
        self.config_mgr = ConfigManager()
        self.conn_mgr = ConnectionManager(self.config_mgr)
        self.active_conn = self.conn_mgr.get_active_connection()
        self.provider = ProviderRegistry.get_provider_for_connection(self.active_conn)
        self.model_name = self.config_mgr.config.active_model or (
            self.active_conn.discovered_models[0].id if self.active_conn.discovered_models else "default"
        )

    def render_market_table(self, quotes: List[StockQuote]) -> Table:
        """Render the 20-stock market overview table."""
        page_title = self.service.get_page_title(self.current_page)
        table = Table(
            title=f"Proton Market Watch — Page {self.current_page}/3: {page_title}",
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("#", style="dim", width=3)
        table.add_column("Symbol", style="bold cyan", width=9)
        table.add_column("Name", style="bold", width=22)
        table.add_column("Price", justify="right", width=12)
        table.add_column("Change ($)", justify="right", width=11)
        table.add_column("Change (%)", justify="right", width=11)
        table.add_column("Day Range", justify="center", width=20)
        table.add_column("Market Cap", justify="right", width=12)

        for idx, q in enumerate(quotes, 1):
            if q.price > 0:
                color = "green" if q.change >= 0 else "red"
                sign = "+" if q.change >= 0 else ""
                price_str = f"${q.price:,.2f}" if q.price >= 1 else f"${q.price:.4f}"
                chg_str = f"[{color}]{sign}${q.change:,.2f}[/{color}]"
                pct_str = f"[{color}]{sign}{q.change_pct:.2f}%[/{color}]"
                range_str = f"${q.day_low:,.2f} - ${q.day_high:,.2f}" if q.day_low > 0 else "N/A"
                mcap_str = self._format_market_cap(q.market_cap)
            else:
                price_str = "[dim]Loading...[/dim]"
                chg_str = "---"
                pct_str = "---"
                range_str = "---"
                mcap_str = "---"

            table.add_row(
                str(idx),
                q.symbol,
                q.name[:22],
                price_str,
                chg_str,
                pct_str,
                range_str,
                mcap_str,
            )

        return table

    def _format_market_cap(self, cap: float) -> str:
        if cap >= 1e12:
            return f"${cap / 1e12:.2f}T"
        elif cap >= 1e9:
            return f"${cap / 1e9:.2f}B"
        elif cap >= 1e6:
            return f"${cap / 1e6:.2f}M"
        elif cap > 0:
            return f"${cap:,.0f}"
        return "N/A"

    async def show_stock_detail(self, symbol: str, timeframe: str = "1mo") -> None:
        """Inspect comprehensive stock fundamentals and interactive price chart."""
        with self.console.status(
            f"[bold cyan]📊 Loading stock data & chart for {symbol.upper()} ({timeframe.upper()})...[/bold cyan]",
            spinner="dots"
        ):
            detail = await self.service.fetch_detail(symbol, timeframe=timeframe)

        if not detail or detail.price <= 0:
            self.console.print(f"[red]Could not retrieve data for symbol '{symbol.upper()}'. Check ticker symbol.[/red]")
            return

        while True:
            os.system("cls" if sys.platform == "win32" else "clear")
            color = "green" if detail.change >= 0 else "red"
            sign = "+" if detail.change >= 0 else ""

            # Header panel
            header = (
                f"[bold cyan]{detail.name}[/bold cyan] [bold bright_white]({detail.symbol})[/bold bright_white]  "
                f"[bold]{detail.sector}[/bold] | [dim]{detail.industry}[/dim]\n"
                f"[bold {color}]${detail.price:,.2f}  {sign}${detail.change:,.2f} ({sign}{detail.change_pct:.2f}%)[/bold {color}]  "
                f"[dim]Currency: {detail.currency}[/dim]"
            )
            self.console.print(Panel(header, border_style=color))

            # Fundamentals Key Metrics Table
            f_table = Table(show_header=True, header_style="bold cyan")
            f_table.add_column("Metric", style="bold")
            f_table.add_column("Value")
            f_table.add_column("Metric", style="bold")
            f_table.add_column("Value")

            pe_val = f"{detail.trailing_pe:.2f}" if detail.trailing_pe else "N/A"
            f_pe_val = f"{detail.forward_pe:.2f}" if detail.forward_pe else "N/A"
            eps_val = f"${detail.eps:.2f}" if detail.eps else "N/A"
            beta_val = f"{detail.beta:.2f}" if detail.beta else "N/A"
            div_val = f"{detail.dividend_yield * 100:.2f}%" if detail.dividend_yield else "N/A"
            tgt_val = f"${detail.target_price:.2f}" if detail.target_price else "N/A"

            f_table.add_row("Open", f"${detail.open_price:,.2f}", "Trailing P/E", pe_val)
            f_table.add_row("Prev Close", f"${detail.prev_close:,.2f}", "Forward P/E", f_pe_val)
            f_table.add_row("Day Range", f"${detail.day_low:,.2f} - ${detail.day_high:,.2f}", "Diluted EPS", eps_val)
            f_table.add_row("52-Wk Range", f"${detail.fifty_two_low:,.2f} - ${detail.fifty_two_high:,.2f}", "Beta (Volatility)", beta_val)
            f_table.add_row("Market Cap", self._format_market_cap(detail.market_cap), "Dividend Yield", div_val)
            f_table.add_row("Volume", f"{detail.volume:,}", "Analyst Target", tgt_val)
            f_table.add_row("Avg Volume", f"{detail.avg_volume:,}", "Recommendation", f"[bold]{detail.recommendation}[/bold]")

            self.console.print(f_table)
            self.console.print()

            # Render Chart
            if detail.history_prices:
                chart_str = render_stock_chart(
                    detail.history_prices,
                    detail.history_dates,
                    symbol=detail.symbol,
                    timeframe=timeframe,
                )
                self.console.print(Panel(chart_str, border_style="cyan"))
            else:
                self.console.print("[dim]No historical chart data available for this timeframe.[/dim]")

            self.console.print(
                f"[bold cyan]Actions:[/bold cyan] "
                f"[dim]Change timeframe: `1d`, `5d`, `1m`, `6m`, `1y` | `analyze` (AI Analysis) | `ask <q>` | `back` to list[/dim]"
            )

            prompt_text = HTML(f"<ansicyan><b>proton-stock</b></ansicyan> [<b>{detail.symbol}</b>] &gt; ")
            try:
                if self.session is not None:
                    user_inp = await self.session.prompt_async(prompt_text)
                else:
                    user_inp = input(f"proton-stock [{detail.symbol}] > ")
            except (KeyboardInterrupt, EOFError):
                break

            sub_cmd = user_inp.strip().lower()
            if not sub_cmd:
                continue

            if sub_cmd in ("back", "b", "exit", "q"):
                break
            elif sub_cmd in ("1d", "5d", "1m", "1mo", "6m", "6mo", "1y", "5y"):
                timeframe = "1mo" if sub_cmd == "1m" else ("6mo" if sub_cmd == "6m" else sub_cmd)
                with self.console.status(
                    f"[bold cyan]📊 Updating chart for {symbol.upper()} ({timeframe.upper()})...[/bold cyan]",
                    spinner="dots"
                ):
                    detail = await self.service.fetch_detail(symbol, timeframe=timeframe)
            elif sub_cmd in ("analyze", "ai", "analysis"):
                await self._run_ai_stock_analysis(detail)
                input("\nPress Enter to return to chart...")
            elif sub_cmd.startswith("ask "):
                q_text = user_inp.strip()[4:].strip()
                await self._ask_ai_about_stock(detail, q_text)
                input("\nPress Enter to return to chart...")
            else:
                # User typed a different ticker symbol directly
                with self.console.status(
                    f"[bold cyan]📊 Loading stock data for {sub_cmd.upper()}...[/bold cyan]",
                    spinner="dots"
                ):
                    new_detail = await self.service.fetch_detail(sub_cmd, timeframe=timeframe)
                if new_detail and new_detail.price > 0:
                    detail = new_detail
                else:
                    self.console.print(f"[yellow]Symbol '{sub_cmd.upper()}' not found.[/yellow]")
                    time.sleep(1.5)

    async def _run_ai_stock_analysis(self, detail: StockDetail) -> None:
        """Run ProAura AI stock analysis on fundamentals and trend."""
        self.console.print(f"\n[bold cyan]ProAura AI is analyzing {detail.name} ({detail.symbol})...[/bold cyan]\n")
        prompt = (
            f"Please perform a financial stock analysis for {detail.name} ({detail.symbol}):\n\n"
            f"- Current Price: ${detail.price:.2f} ({detail.change_pct:+.2f}%)\n"
            f"- 52-Week Range: ${detail.fifty_two_low:.2f} - ${detail.fifty_two_high:.2f}\n"
            f"- Market Cap: {self._format_market_cap(detail.market_cap)}\n"
            f"- Trailing P/E: {detail.trailing_pe}, Forward P/E: {detail.forward_pe}\n"
            f"- EPS: ${detail.eps}, Beta: {detail.beta}\n"
            f"- Sector: {detail.sector}, Industry: {detail.industry}\n"
            f"- Wall Street Recommendation: {detail.recommendation}, Target Price: ${detail.target_price}\n\n"
            f"Provide an executive summary covering: 1) Valuation & Health, 2) Growth Drivers, 3) Key Risks, 4) Overall Outlook."
        )
        await self._stream_ai(prompt)

    async def _ask_ai_about_stock(self, detail: StockDetail, question: str) -> None:
        """Answer specific user question about the active stock."""
        self.console.print(f"\n[bold cyan]ProAura AI answering about {detail.symbol}...[/bold cyan]\n")
        prompt = (
            f"Stock Context: {detail.name} ({detail.symbol}), Price: ${detail.price:.2f}, Sector: {detail.sector}, P/E: {detail.trailing_pe}.\n\n"
            f"Question: {question}\n\n"
            f"Please answer concisely and accurately based on market fundamentals."
        )
        await self._stream_ai(prompt)

    async def _stream_ai(self, prompt: str) -> None:
        from proton.core.types import Message, Role
        messages = [
            Message(
                role=Role.SYSTEM,
                content="You are ProAura, the expert financial AI analyst in Proton. Provide clear, balanced market insights."
            ),
            Message(role=Role.USER, content=prompt),
        ]
        status = self.console.status("[bold cyan]Analyzing market data...[/bold cyan]", spinner="dots")
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
            self.console.print(f"\n[red]AI Analysis Error: {e}[/red]\n")

    async def run(self) -> None:
        """Main stock dashboard loop with live 10-second auto-refresh and spinning loading bar."""
        # If user passed initial symbol directly (e.g. `proton stock AAPL`)
        if self.initial_symbol:
            await self.show_stock_detail(self.initial_symbol)
            return

        os.system("cls" if sys.platform == "win32" else "clear")

        while True:
            # Fetch 20 stocks for current page with animated loading spinner + stock symbol preview
            symbols = self.service.get_symbols_for_page(self.current_page)
            sym_preview = ", ".join(symbols[:5])
            with self.console.status(
                f"[bold cyan]📈 Loading {len(symbols)} Live Stocks (Page {self.current_page}: {sym_preview}...)[/bold cyan]",
                spinner="dots"
            ):
                quotes = await self.service.fetch_page_quotes(self.current_page)

            os.system("cls" if sys.platform == "win32" else "clear")

            table = self.render_market_table(quotes)
            self.console.print(table)

            now_str = datetime.now().strftime("%I:%M:%S %p")
            status_line = (
                f"[dim]────────────────────────────────────────────────────────────────────────────────────────[/dim]\n"
                f"[bold green]● LIVE (10s Auto-Refresh)[/bold green] [dim]Updated: {now_str}[/dim]  "
                f"[bold]|[/bold]  Page [bold cyan]{self.current_page}/3[/bold cyan]  "
                f"[bold]|[/bold]  [dim]Type [1-20] or Symbol (e.g. `AAPL`, `NVDA`) to inspect chart[/dim]\n"
                f"[dim]Controls: `next` / `n` (Next Page) | `prev` / `p` | `page <1-3>` | `refresh` / `r` | `exit` / `q`[/dim]"
            )
            self.console.print(status_line)

            # Wait for user input with 10-second refresh timeout
            prompt_text = HTML(f"<ansicyan><b>proton-stock</b></ansicyan> [<b>Page {self.current_page}</b>] &gt; ")

            user_cmd = None
            try:
                if self.session is not None:
                    # Async prompt with 10-second timeout for live ticker refresh
                    try:
                        user_cmd = await asyncio.wait_for(self.session.prompt_async(prompt_text), timeout=10.0)
                    except asyncio.TimeoutError:
                        # Auto-refresh cycle every 10 seconds
                        continue
                else:
                    user_cmd = input(f"proton-stock [Page {self.current_page}] > ")
            except (KeyboardInterrupt, EOFError):
                break

            if not user_cmd:
                continue

            cmd = user_cmd.strip()
            lower_cmd = cmd.lower()

            if lower_cmd in ("exit", "quit", "q"):
                self.console.print("[dim]Exiting Proton Stock Market Tracker. Goodbye![/dim]")
                break

            elif lower_cmd in ("next", "n", "page down"):
                self.current_page = 1 if self.current_page >= self.service.get_total_pages() else self.current_page + 1

            elif lower_cmd in ("prev", "p", "page up"):
                self.current_page = self.service.get_total_pages() if self.current_page <= 1 else self.current_page - 1

            elif lower_cmd.startswith("page "):
                p_arg = lower_cmd[5:].strip()
                if p_arg.isdigit():
                    self.current_page = max(1, min(self.service.get_total_pages(), int(p_arg)))

            elif lower_cmd in ("refresh", "r"):
                continue

            # Check if user entered a numbered stock index [1-20]
            elif cmd.isdigit():
                idx = int(cmd)
                symbols = self.service.get_symbols_for_page(self.current_page)
                if 1 <= idx <= len(symbols):
                    target_sym = symbols[idx - 1]
                    await self.show_stock_detail(target_sym)
                else:
                    self.console.print(f"[yellow]Please enter a valid stock index [1-{len(symbols)}].[/yellow]")
                    time.sleep(1.0)

            else:
                # Treat as stock ticker symbol (e.g. `AAPL`, `NVDA`, `TSLA`, `BTC-USD`)
                await self.show_stock_detail(cmd)
