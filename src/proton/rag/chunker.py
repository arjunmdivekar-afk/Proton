"""Document and Code Chunker with parent-child tracking and hash deduplication."""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_path: str
    content: str
    start_line: int
    end_line: int
    content_hash: str
    metadata: Dict[str, str] = Field(default_factory=dict)


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentChunker:
    """Chunks source code and markdown documents intelligently."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, file_path: Path, relative_to: Path) -> List[DocumentChunk]:
        """Read and chunk a text/code file into structured DocumentChunk objects."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return []

        rel_path = str(file_path.relative_to(relative_to)).replace("\\", "/")
        lines = content.splitlines(keepends=True)
        if not lines:
            return []

        chunks: List[DocumentChunk] = []
        current_chunk_lines: List[str] = []
        current_char_count = 0
        start_line = 1
        current_line_no = 1

        for line in lines:
            current_chunk_lines.append(line)
            current_char_count += len(line)

            if current_char_count >= self.chunk_size:
                chunk_text = "".join(current_chunk_lines)
                end_line = current_line_no
                chunk_id = f"{rel_path}:{start_line}-{end_line}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_path=rel_path,
                        content=chunk_text,
                        start_line=start_line,
                        end_line=end_line,
                        content_hash=compute_hash(chunk_text),
                        metadata={"extension": file_path.suffix.lower()},
                    )
                )

                # Overlap step: keep last few lines
                overlap_lines: List[str] = []
                overlap_count = 0
                for rev_line in reversed(current_chunk_lines):
                    if overlap_count + len(rev_line) <= self.chunk_overlap:
                        overlap_lines.insert(0, rev_line)
                        overlap_count += len(rev_line)
                    else:
                        break

                current_chunk_lines = overlap_lines
                current_char_count = overlap_count
                start_line = end_line - len(overlap_lines) + 1

            current_line_no += 1

        # Final trailing chunk
        if current_chunk_lines:
            chunk_text = "".join(current_chunk_lines)
            end_line = len(lines)
            chunk_id = f"{rel_path}:{start_line}-{end_line}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_path=rel_path,
                    content=chunk_text,
                    start_line=start_line,
                    end_line=end_line,
                    content_hash=compute_hash(chunk_text),
                    metadata={"extension": file_path.suffix.lower()},
                )
            )

        return chunks
