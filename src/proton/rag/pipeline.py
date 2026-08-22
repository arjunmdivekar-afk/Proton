"""End-to-end RAG indexing and retrieval pipeline."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from proton.rag.chunker import DocumentChunker, DocumentChunk
from proton.rag.hybrid_store import SQLiteHybridVectorStore, SearchResult
from proton.providers.base import ModelProvider
from proton.core.config import get_proton_home, RAGConfig


SUPPORTED_EXTENSIONS = {
    ".py", ".md", ".txt", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
    ".json", ".yaml", ".yml", ".toml", ".sql", ".sh", ".ps1", ".rs", ".go"
}

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".proton"}


class IndexStats(BaseModel):
    files_indexed: int = 0
    chunks_created: int = 0
    duration_seconds: float = 0.0


class RAGPipeline:
    """Manages document chunking, embeddings, indexing, and retrieval."""

    def __init__(
        self,
        workspace_root: Path,
        provider: Optional[ModelProvider] = None,
        config: Optional[RAGConfig] = None,
    ) -> None:
        self.workspace_root = workspace_root.resolve()
        self.config = config or RAGConfig()
        db_path = Path(self.config.db_path) if self.config.db_path else (get_proton_home() / "rag_index.db")
        self.store = SQLiteHybridVectorStore(db_path)
        self.chunker = DocumentChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        self.provider = provider

    def set_provider(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def index_directory(self, target_dir: Optional[Path] = None) -> IndexStats:
        """Scan directory, chunk documents, compute embeddings, and store in SQLite vector index."""
        scan_root = (target_dir or self.workspace_root).resolve()
        all_chunks: List[DocumentChunk] = []
        files_count = 0

        for root, dirs, files in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    chunks = self.chunker.chunk_file(file_path, relative_to=self.workspace_root)
                    if chunks:
                        all_chunks.extend(chunks)
                        files_count += 1

        if not all_chunks:
            return IndexStats(files_indexed=0, chunks_created=0)

        # Generate embeddings if provider available
        embeddings: Optional[List[List[float]]] = None
        if self.provider:
            texts = [c.content for c in all_chunks]
            # Embed in batches of 32
            embeddings = []
            batch_size = 32
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_emb = await self.provider.embed(batch)
                embeddings.extend(batch_emb)

        self.store.add_chunks(all_chunks, embeddings)
        return IndexStats(files_indexed=files_count, chunks_created=len(all_chunks))

    async def search(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        """Search relevant chunks with vector + lexical ranking and citations."""
        k = top_k or self.config.top_k
        query_emb: Optional[List[float]] = None
        if self.provider:
            res = await self.provider.embed([query])
            if res:
                query_emb = res[0]

        return self.store.search(
            query_text=query,
            query_embedding=query_emb,
            top_k=k,
            min_score=self.config.min_similarity,
        )
