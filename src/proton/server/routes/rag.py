"""RAG & Knowledge Base API routes."""

from pathlib import Path
from typing import List
from fastapi import APIRouter

from proton.server.schemas import RagSearchRequest, RagSearchResponse
from proton.core.config import get_proton_home
from proton.rag.hybrid_store import SQLiteHybridVectorStore
from proton.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/v1/rag", tags=["Knowledge & RAG"])


@router.post("/search", response_model=RagSearchResponse)
async def search_rag(req: RagSearchRequest):
    """Search knowledge base with hybrid BM25 and cosine distance matching."""
    db_path = get_proton_home() / "rag_index.db"
    store = SQLiteHybridVectorStore(db_path)
    results = store.search(query=req.query, top_k=req.top_k, min_similarity=req.min_similarity)

    formatted = [
        {
            "chunk_id": r.chunk_id,
            "doc_path": r.doc_path,
            "content": r.content,
            "score": r.score,
            "citation": r.citation,
            "lines": f"{r.start_line}-{r.end_line}",
        }
        for r in results
    ]

    return RagSearchResponse(
        query=req.query,
        results=formatted,
        total=len(formatted),
    )


@router.post("/index")
async def index_workspace(workspace: str = None):
    """Index codebase files into local SQLite vector store."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    pipeline = RAGPipeline(ws)
    stats = await pipeline.index_directory()
    return {
        "status": "success",
        "workspace": str(ws),
        "files_indexed": stats.files_indexed,
        "chunks_indexed": stats.chunks_created,
    }


@router.get("/status")
async def get_rag_status():
    """Get total indexed documents and database statistics."""
    db_path = get_proton_home() / "rag_index.db"
    store = SQLiteHybridVectorStore(db_path)
    count = store.count()
    return {
        "status": "active",
        "database_path": str(db_path),
        "total_chunks": count,
    }
