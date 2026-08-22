"""Unit tests for RAG chunker and hybrid vector store."""

import pytest
from pathlib import Path
from proton.rag.chunker import DocumentChunker
from proton.rag.hybrid_store import SQLiteHybridVectorStore
from proton.rag.pipeline import RAGPipeline


def test_document_chunker(tmp_path: Path):
    doc_file = tmp_path / "docs.md"
    doc_file.write_text("# Title\n\nThis is paragraph one.\n\nThis is paragraph two.", encoding="utf-8")

    chunker = DocumentChunker(chunk_size=30, chunk_overlap=10)
    chunks = chunker.chunk_file(doc_file, relative_to=tmp_path)
    assert len(chunks) >= 1
    assert chunks[0].doc_path == "docs.md"
    assert chunks[0].content_hash != ""


@pytest.mark.asyncio
async def test_hybrid_vector_store_and_pipeline(tmp_path: Path):
    db_path = tmp_path / "rag.db"
    store = SQLiteHybridVectorStore(db_path)

    # Index some test documents
    doc1 = tmp_path / "auth.py"
    doc1.write_text("def authenticate(username, password):\n    # JWT token validator\n    return True\n", encoding="utf-8")

    pipeline = RAGPipeline(workspace_root=tmp_path)
    pipeline.store = store

    stats = await pipeline.index_directory()
    assert stats.files_indexed >= 1
    assert store.count() >= 1

    # Search
    results = await pipeline.search(query="JWT token authenticate")
    assert len(results) >= 1
    assert results[0].doc_path == "auth.py"
    assert "[auth.py:" in results[0].citation
