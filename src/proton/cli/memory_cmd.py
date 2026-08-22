"""CLI commands for Proton Explicit Categorized Memory (`proton memory`)."""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from proton.memory.manager import memory_manager
from proton.memory.store import MemoryType

memory_app = typer.Typer(
    help="Manage categorized project & user memories (PROJECT, DECISION, PREFERENCE, FACT, TASK, USER, SESSION).",
    no_args_is_help=False,
)
console = Console(safe_box=True)

CATEGORY_COLORS = {
    MemoryType.PROJECT: "cyan",
    MemoryType.DECISION: "bright_magenta",
    MemoryType.PREFERENCE: "yellow",
    MemoryType.FACT: "green",
    MemoryType.TASK: "bright_blue",
    MemoryType.USER: "bright_cyan",
    MemoryType.SESSION: "dim",
}


@memory_app.callback(invoke_without_command=True)
def default_memory_callback(
    ctx: typer.Context,
    mem_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by category: USER, PROJECT, SESSION, PREFERENCE, FACT, DECISION, TASK"),
) -> None:
    """List categorized memory items, or run subcommands."""
    if ctx.invoked_subcommand is not None:
        return
    list_memories_cmd(mem_type=mem_type)


@memory_app.command("list")
def list_memories_cmd(
    mem_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by category: USER, PROJECT, SESSION, PREFERENCE, FACT, DECISION, TASK"),
) -> None:
    """List all stored memory items categorized by explicit memory type."""
    m_type = MemoryType.from_str(mem_type) if mem_type else None
    records = memory_manager.list_all(memory_type=m_type)

    if not records:
        filter_str = f" for category '[cyan]{m_type.value}[/cyan]'" if m_type else ""
        console.print(f"[yellow]No persistent memory records found{filter_str}.[/yellow]")
        console.print("[dim]Add a memory using:[/dim] [bold bright_white]proton memory add \"<content>\" --type DECISION[/bold bright_white]\n")
        return

    table = Table(
        title=f"🧠 Proton Persistent Memory ({len(records)} items" + (f" in {m_type.value}" if m_type else "") + ")",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", justify="right", style="bold", width=6)
    table.add_column("Category", style="bold", width=14)
    table.add_column("Memory Content", width=55)
    table.add_column("Created", style="dim", width=18)

    for r in records:
        cat_color = CATEGORY_COLORS.get(r.memory_type, "white")
        created_str = r.created_at.strftime("%Y-%m-%d %H:%M")
        table.add_row(
            str(r.id),
            f"[{cat_color}]{r.memory_type.value}[/{cat_color}]",
            r.content,
            created_str,
        )

    console.print(table)
    console.print(
        "\n[dim]Categories: `PROJECT` | `DECISION` | `PREFERENCE` | `FACT` | `TASK` | `USER` | `SESSION`\n"
        "Commands: `proton memory add \"...\" --type <CAT>`, `proton memory search \"...\"`, `proton memory forget <ID>`[/dim]\n"
    )


@memory_app.command("add")
def add_memory_cmd(
    content: str = typer.Argument(..., help="Fact, decision, rule, or preference to remember"),
    mem_type: str = typer.Option("PROJECT", "--type", "-t", help="Category: USER, PROJECT, SESSION, PREFERENCE, FACT, DECISION, TASK"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Optional short identifier"),
) -> None:
    """Add a new explicitly categorized memory item."""
    m_type = MemoryType.from_str(mem_type)
    rec = memory_manager.remember(content=content, memory_type=m_type, key=key)
    cat_color = CATEGORY_COLORS.get(m_type, "white")

    console.print(
        Panel.fit(
            f"[bold green]✓ Memory Stored Successfully![/bold green]\n\n"
            f"• [bold]ID:[/bold] [cyan]{rec.id}[/cyan]\n"
            f"• [bold]Category:[/bold] [{cat_color}]{rec.memory_type.value}[/{cat_color}]\n"
            f"• [bold]Content:[/bold] {rec.content}\n"
            f"• [bold]Created At:[/bold] [dim]{rec.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}[/dim]",
            border_style="green",
        )
    )


@memory_app.command("search")
def search_memory_cmd(
    query: str = typer.Argument(..., help="Search query keywords"),
    mem_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by category"),
) -> None:
    """Search stored memories by keyword or category."""
    m_type = MemoryType.from_str(mem_type) if mem_type else None
    results = memory_manager.recall(query=query, memory_type=m_type)

    if not results:
        console.print(f"[yellow]No memories matching '{query}' found.[/yellow]")
        return

    table = Table(title=f"Memory Search Results for '{query}' ({len(results)} matches)", show_header=True, header_style="bold cyan")
    table.add_column("ID", justify="right", style="bold", width=6)
    table.add_column("Category", style="bold", width=14)
    table.add_column("Memory Content", width=60)

    for r in results:
        cat_color = CATEGORY_COLORS.get(r.memory_type, "white")
        table.add_row(
            str(r.id),
            f"[{cat_color}]{r.memory_type.value}[/{cat_color}]",
            r.content,
        )

    console.print(table)


@memory_app.command("forget")
def forget_memory_cmd(
    record_id: int = typer.Argument(..., help="Numeric ID of memory to delete"),
) -> None:
    """Delete a specific memory item by ID."""
    success = memory_manager.forget(record_id)
    if success:
        console.print(f"[bold green]✓ Deleted memory item #{record_id}.[/bold green]")
    else:
        console.print(f"[bold red]✗ Memory item #{record_id} not found.[/bold red]")


@memory_app.command("export")
def export_memory_cmd(
    format_type: str = typer.Option("md", "--format", "-f", help="Export format: 'md' (Markdown) or 'json'"),
    file_path: Optional[str] = typer.Option(None, "--file", "-o", help="File path to write export to"),
) -> None:
    """Export all categorized memories as Markdown or JSON."""
    records = memory_manager.list_all()

    if format_type.lower() == "json":
        data = [r.model_dump(mode="json") for r in records]
        out_str = json.dumps(data, indent=2)
    else:
        # Group by category
        grouped = {}
        for r in records:
            cat = r.memory_type.value
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(r)

        lines = ["# 🧠 Proton Persistent Memory Export\n"]
        for cat, items in grouped.items():
            lines.append(f"## {cat}\n")
            for it in items:
                created_str = it.created_at.strftime("%Y-%m-%d %H:%M")
                lines.append(f"- **ID #{it.id}:** {it.content} *(Added: {created_str})*")
            lines.append("")
        out_str = "\n".join(lines)

    if file_path:
        Path(file_path).write_text(out_str, encoding="utf-8")
        console.print(f"[bold green]✓ Exported {len(records)} memories to `{file_path}`.[/bold green]")
    else:
        console.print(out_str)


@memory_app.command("clear")
def clear_memory_cmd(
    mem_type: Optional[str] = typer.Option(None, "--type", "-t", help="Category to clear (clears all if omitted)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Clear all or category-specific memories."""
    m_type = MemoryType.from_str(mem_type) if mem_type else None
    target_str = f"category '{m_type.value}'" if m_type else "ALL persistent memories"

    if not yes:
        confirm = typer.confirm(f"Are you sure you want to clear {target_str}?")
        if not confirm:
            console.print("[dim]Operation cancelled.[/dim]")
            return

    count = memory_manager.clear(memory_type=m_type)
    console.print(f"[bold green]✓ Cleared {count} memory item(s) from {target_str}.[/bold green]")
