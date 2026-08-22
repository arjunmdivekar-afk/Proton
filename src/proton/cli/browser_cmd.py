"""CLI command for launching Proton Browser."""

import asyncio
from typing import Optional
import typer

from proton.browser.app import ProtonBrowserApp


def launch_browser(
    target: Optional[str] = typer.Argument(
        None,
        help="Optional initial URL or search query (e.g. `proton browser react.dev` or `proton browser 'python tutorial'`)",
    ),
    ai_mode: bool = typer.Option(
        False,
        "--ai_mode",
        "--ai-mode",
        "-a",
        help="Launch Proton Browser with AI Copilot enabled",
    ),
) -> None:
    """Launch Proton Browser — a keyboard-first terminal web browser with live DuckDuckGo search, clickable numbered links, and Proton AI Copilot."""
    app = ProtonBrowserApp(ai_mode=ai_mode, initial_target=target)
    asyncio.run(app.run())
