"""RAG & Knowledge Base API routes with Python client examples."""

from pathlib import Path
from typing import List
from fastapi import APIRouter

from proton.server.schemas import RagSearchRequest, RagSearchResponse
from proton.core.config import get_proton_home
from proton.rag.hybrid_store import SQLiteHybridVectorStore
from proton.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/v1/rag", tags=["Knowledge & RAG"])


@router.post(
    "/search",
    summary="Hybrid Vector & BM25 Search",
    response_model=RagSearchResponse,
)
async def search_rag(req: RagSearchRequest):
    """
    Search SQLite vector store using combined BM25 keyword matching and cosine embedding distance.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/rag/search"
    payload = {
        "query": "hybrid vector BM25 similarity scoring",
        "top_k": 3,
        "min_similarity": 0.25
    }

    response = requests.post(url, json=payload)
    results = response.json()
    print(f"Total Matches: {results['total']}")
    for r in results["results"]:
        print(f"- [{r['score']:.2f}] {r['citation']}")
    ```
    """
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


@router.post(
    "/index",
    summary="Index Workspace Codebase",
)
async def index_workspace(workspace: str = None):
    """
    Scan workspace files, create parent-child chunks, and compute vector embeddings in SQLite.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/rag/index"
    response = requests.post(url)
    print("Indexing Complete:", response.json())
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    pipeline = RAGPipeline(ws)
    stats = await pipeline.index_directory()
    return {
        "status": "success",
        "workspace": str(ws),
        "files_indexed": stats.files_indexed,
        "chunks_indexed": stats.chunks_created,
    }


@router.get(
    "/status",
    summary="Get RAG Knowledge Store Status",
)
async def get_rag_status():
    """
    Get indexed chunk counts and SQLite vector database path.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/rag/status"
    response = requests.get(url)
    print("RAG Status:", response.json())
    ```
    """
    db_path = get_proton_home() / "rag_index.db"
    store = SQLiteHybridVectorStore(db_path)
    count = store.count()
    return {
        "status": "active",
        "database_path": str(db_path),
        "total_chunks": count,
    }
