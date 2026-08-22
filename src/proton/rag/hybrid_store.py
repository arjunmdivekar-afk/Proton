"""In-process hybrid vector and BM25 store backed by SQLite."""

import sqlite3
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from proton.rag.chunker import DocumentChunk


class SearchResult(BaseModel):
    chunk_id: str
    doc_path: str
    content: str
    start_line: int
    end_line: int
    score: float
    vector_score: float = 0.0
    bm25_score: float = 0.0
    citation: str


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    if n1 <= 0 or n2 <= 0:
        return 0.0
    return dot / (n1 * n2)


class SQLiteHybridVectorStore:
    """Local-first hybrid vector store storing chunks, embeddings, and full-text indexes."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    doc_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding_json TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_path ON rag_chunks(doc_path)")
            conn.commit()

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: Optional[List[List[float]]] = None) -> int:
        """Insert or replace document chunks and vector embeddings."""
        if not chunks:
            return 0

        with sqlite3.connect(str(self.db_path)) as conn:
            for i, chunk in enumerate(chunks):
                emb_json = json.dumps(embeddings[i]) if embeddings and i < len(embeddings) else None
                conn.execute(
                    """
                    INSERT OR REPLACE INTO rag_chunks 
                    (chunk_id, doc_path, content, start_line, end_line, content_hash, embedding_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.chunk_id,
                        chunk.doc_path,
                        chunk.content,
                        chunk.start_line,
                        chunk.end_line,
                        chunk.content_hash,
                        emb_json,
                        json.dumps(chunk.metadata),
                    ),
                )
            conn.commit()
        return len(chunks)

    def delete_by_doc_path(self, doc_path: str) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM rag_chunks WHERE doc_path = ?", (doc_path,))
            conn.commit()

    def search(
        self,
        query_text: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        min_score: float = 0.1,
    ) -> List[SearchResult]:
        """Perform hybrid search combining vector cosine similarity and term matching."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id, doc_path, content, start_line, end_line, embedding_json FROM rag_chunks")
            rows = cursor.fetchall()

        if not rows:
            return []

        query_terms = set(query_text.lower().split())
        results: List[SearchResult] = []

        for chunk_id, doc_path, content, start_line, end_line, emb_json in rows:
            # 1. Vector similarity
            vec_score = 0.0
            if query_embedding and emb_json:
                try:
                    chunk_emb = json.loads(emb_json)
                    vec_score = max(0.0, cosine_similarity(query_embedding, chunk_emb))
                except Exception:
                    vec_score = 0.0

            # 2. Keyword term frequency (BM25-like proxy)
            content_lower = content.lower()
            term_matches = sum(1 for term in query_terms if term in content_lower)
            lexical_score = (term_matches / len(query_terms)) if query_terms else 0.0

            # Hybrid score weighting: 70% vector + 30% lexical keyword
            hybrid_score = (0.7 * vec_score) + (0.3 * lexical_score) if query_embedding else lexical_score

            if hybrid_score >= min_score:
                results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        doc_path=doc_path,
                        content=content,
                        start_line=start_line,
                        end_line=end_line,
                        score=round(hybrid_score, 4),
                        vector_score=round(vec_score, 4),
                        bm25_score=round(lexical_score, 4),
                        citation=f"[{doc_path}:{start_line}-{end_line}]",
                    )
                )

        # Sort descending by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def count(self) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM rag_chunks")
            return cur.fetchone()[0]
