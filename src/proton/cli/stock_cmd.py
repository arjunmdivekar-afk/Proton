"""CLI command for Proton Stock Market Tracker (`proton stock`)."""

import asyncio
from typing import Optional
import typer

from proton.stocks.app import ProtonStockApp


def launch_stock_dashboard(
    symbol: Optional[str] = typer.Argument(
        None,
        help="Optional stock ticker symbol to inspect directly (e.g. `proton stock AAPL` or `proton stock NVDA`)",
    ),
    page: int = typer.Option(
        1,
        "--page",
        "-p",
        help="Market watch page number (1: Tech Giants & AI, 2: Blue Chips & Healthcare, 3: Global Indices & Crypto)",
    ),
) -> None:
    """Launch Proton Stock Market Tracker — Live quotes with 2-second auto-refresh, 20 stocks per page, and detailed price charts."""
    app = ProtonStockApp(initial_symbol=symbol, page=page)
    asyncio.run(app.run())
