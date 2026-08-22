"""Coding knowledge corpus builder and downloader for Proton RAG."""

import os
from pathlib import Path
from typing import Dict, List, Optional
import httpx

from proton.core.config import get_proton_home


# Curated programming topics and standard references
KNOWLEDGE_TOPICS = [
    {
        "filename": "python_core_and_algorithms.md",
        "title": "Python Core Architecture, Data Structures, and Standard Library Algorithms",
        "url": "https://raw.githubusercontent.com/TheAlgorithms/Python/master/README.md",
    },
    {
        "filename": "javascript_algorithms_and_patterns.md",
        "title": "JavaScript and TypeScript Design Patterns, Data Structures, and Best Practices",
        "url": "https://raw.githubusercontent.com/trekhleb/javascript-algorithms/master/README.md",
    },
    {
        "filename": "system_design_and_architecture.md",
        "title": "System Design Primer, Scalability, Caching, Databases, and Microservices",
        "url": "https://raw.githubusercontent.com/donnemartin/system-design-primer/master/README.md",
    },
    {
        "filename": "clean_code_and_refactoring.md",
        "title": "Clean Code Handbook, Refactoring Patterns, and SOLID Principles",
        "url": "https://raw.githubusercontent.com/ryanmcdermott/clean-code-javascript/master/README.md",
    },
]


async def fetch_and_build_knowledge_corpus(output_dir: Optional[Path] = None) -> List[Path]:
    """Download and assemble structured programming knowledge documents for RAG indexing."""
    target_dir = output_dir or (get_proton_home() / "knowledge")
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_files: List[Path] = []

    headers = {
        "User-Agent": "Proton-AI-Assistant/1.4.0 (Coding Knowledge Ingestor)",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for topic in KNOWLEDGE_TOPICS:
            dest_file = target_dir / topic["filename"]
            try:
                resp = await client.get(topic["url"], headers=headers)
                if resp.status_code == 200 and resp.text:
                    content = f"# {topic['title']}\n\n" + resp.text
                    with open(dest_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    saved_files.append(dest_file)
            except Exception:
                pass

    return saved_files
