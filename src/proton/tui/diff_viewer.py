"""Syntax-highlighted Diff Viewer for Proton."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def render_diff(diff_str: str, title: str = "Code Changes") -> None:
    """Render unified diff with colored additions and deletions."""
    console = Console()
    if not diff_str.strip():
        console.print("[dim]No changes to display.[/dim]")
        return

    text = Text()
    for line in diff_str.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            text.append(line + "\n", style="bold cyan")
        elif line.startswith("@@"):
            text.append(line + "\n", style="bold magenta")
        elif line.startswith("+"):
            text.append(line + "\n", style="green")
        elif line.startswith("-"):
            text.append(line + "\n", style="red")
        else:
            text.append(line + "\n", style="dim")

    console.print(Panel(text, title=f"[bold]{title}[/bold]", border_style="blue"))
