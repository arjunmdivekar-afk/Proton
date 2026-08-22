"""Rich Theme and styling definitions for Proton."""

from rich.theme import Theme

PROTON_THEME = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "agent": "bold blue",
    "user": "bold magenta",
    "tool": "cyan",
    "chip": "bold white on blue",
})
