"""RAG tools for semantic knowledge retrieval and repository indexing."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.rag.pipeline import RAGPipeline


class RAGSearchArgs(BaseModel):
    query: str = Field(description="Natural language query or question about the codebase/docs")
    top_k: int = Field(default=5, description="Number of source chunks to retrieve")


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "Search indexed project documentation and source code with verified citations."
    risk_level = RiskLevel.SAFE
    args_schema = RAGSearchArgs

    def __init__(self, rag_pipeline: RAGPipeline) -> None:
        self.pipeline = rag_pipeline

    async def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        results = await self.pipeline.search(query=query, top_k=top_k)
        if not results:
            return {"results": [], "message": "No indexed content matched your query."}

        formatted = [
            {
                "citation": r.citation,
                "file": r.doc_path,
                "lines": f"{r.start_line}-{r.end_line}",
                "score": r.score,
                "content": r.content,
            }
            for r in results
        ]
        return {"query": query, "count": len(formatted), "results": formatted}


class RAGIndexArgs(BaseModel):
    path: str = Field(default=".", description="Target folder to index (default: current workspace)")


class RAGIndexTool(BaseTool):
    name = "rag_index"
    description = "Build or refresh the vector and keyword RAG index for workspace files."
    risk_level = RiskLevel.MODIFICATION
    args_schema = RAGIndexArgs

    def __init__(self, rag_pipeline: RAGPipeline) -> None:
        self.pipeline = rag_pipeline

    async def run(self, path: str = ".") -> Dict[str, Any]:
        target = (self.pipeline.workspace_root / path).resolve()
        stats = await self.pipeline.index_directory(target)
        return {
            "success": True,
            "files_indexed": stats.files_indexed,
            "chunks_created": stats.chunks_created,
            "total_chunks_in_db": self.pipeline.store.count(),
        }
