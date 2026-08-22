"""RAG CLI commands (`proton rag`)."""

import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from proton.rag.pipeline import RAGPipeline
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry
from proton.core.config import ConfigManager

rag_app = typer.Typer(help="Manage repository RAG knowledge indexing and search")
console = Console()


@rag_app.command("index")
def index_cmd(
    path: str = typer.Option(".", "--path", "-p", help="Path to index (default: current directory)")
) -> None:
    """Index source code and documentation in workspace for RAG search."""
    workspace = Path.cwd()
    config_mgr = ConfigManager(workspace)
    conn_mgr = ConnectionManager(config_mgr)
    active_conn = conn_mgr.get_active_connection()
    provider = ProviderRegistry.get_provider_for_connection(active_conn)

    pipeline = RAGPipeline(workspace_root=workspace, provider=provider, config=config_mgr.config.rag)

    console.print(f"[cyan]Scanning and indexing files in '{path}'...[/cyan]")
    target = (workspace / path).resolve()
    stats = asyncio.run(pipeline.index_directory(target))
    console.print(f"[bold green]✓ Indexed {stats.files_indexed} files ({stats.chunks_created} chunks) into SQLite vector index.[/bold green]")
    console.print(f"Total chunks in RAG database: [bold cyan]{pipeline.store.count()}[/bold cyan]")


@rag_app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Query to search"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Max results to return")
) -> None:
    """Perform hybrid search on indexed knowledge."""
    workspace = Path.cwd()
    config_mgr = ConfigManager(workspace)
    conn_mgr = ConnectionManager(config_mgr)
    active_conn = conn_mgr.get_active_connection()
    provider = ProviderRegistry.get_provider_for_connection(active_conn)

    pipeline = RAGPipeline(workspace_root=workspace, provider=provider, config=config_mgr.config.rag)
    results = asyncio.run(pipeline.search(query=query, top_k=top_k))

    if not results:
        console.print("[yellow]No matches found. Try running `proton rag index` first.[/yellow]")
        return

    table = Table(title=f"RAG Search Results for '{query}'", show_header=True, header_style="bold cyan")
    table.add_column("Score", justify="right", width=8)
    table.add_column("Citation / File", style="bold")
    table.add_column("Snippet")

    from rich.markup import escape
    for r in results:
        snippet = escape(r.content.replace("\n", " ")[:150]) + "..."
        table.add_row(f"{r.score:.3f}", escape(r.citation), snippet)

    console.print(table)


@rag_app.command("status")
def status_cmd() -> None:
    """Show RAG index statistics."""
    workspace = Path.cwd()
    config_mgr = ConfigManager(workspace)
    pipeline = RAGPipeline(workspace_root=workspace, config=config_mgr.config.rag)
    count = pipeline.store.count()
    console.print(f"[bold]RAG Store Database:[/bold] {pipeline.store.db_path}")
    console.print(f"[bold]Total Indexed Chunks:[/bold] [cyan]{count}[/cyan]")


@rag_app.command("fetch-knowledge")
def fetch_knowledge_cmd(
    target_dir: Optional[str] = typer.Option(None, "--dir", "-d", help="Directory to save downloaded coding knowledge"),
) -> None:
    """Download comprehensive programming knowledge datasets and index them into Proton's vector store."""
    from proton.rag.corpus_fetcher import fetch_and_build_knowledge_corpus
    from proton.core.config import get_proton_home

    dest = Path(target_dir).resolve() if target_dir else (get_proton_home() / "knowledge")
    console.print(f"[cyan]Downloading coding knowledge corpus to {dest}...[/cyan]")
    saved_files = asyncio.run(fetch_and_build_knowledge_corpus(dest))

    if saved_files:
        console.print(f"[bold green]✓ Downloaded {len(saved_files)} programming knowledge guides.[/bold green]")
        console.print("[cyan]Indexing knowledge corpus into RAG vector store...[/cyan]")
        workspace = Path.cwd()
        config_mgr = ConfigManager(workspace)
        conn_mgr = ConnectionManager(config_mgr)
        active_conn = conn_mgr.get_active_connection()
        provider = ProviderRegistry.get_provider_for_connection(active_conn)
        pipeline = RAGPipeline(workspace_root=workspace, provider=provider, config=config_mgr.config.rag)
        stats = asyncio.run(pipeline.index_directory(dest))
        console.print(f"[bold green]✓ Indexed {stats.files_indexed} files ({stats.chunks_created} chunks) into knowledge base![/bold green]")
        console.print(f"Total knowledge chunks available to AI: [bold cyan]{pipeline.store.count()}[/bold cyan]")
    else:
        console.print("[yellow]Could not download knowledge files (check internet connection).[/yellow]")

