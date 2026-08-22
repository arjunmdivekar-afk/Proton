"""Filesystem tools with workspace sandbox enforcement."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.security.sandbox import FilesystemSandbox


class ReadFileArgs(BaseModel):
    path: str = Field(description="Relative path to file inside workspace")
    offset: int = Field(default=0, description="Line offset to start reading from")
    limit: int = Field(default=200, description="Max number of lines to read")


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file within the workspace."
    risk_level = RiskLevel.SAFE
    args_schema = ReadFileArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, path: str, offset: int = 0, limit: int = 200) -> Dict[str, Any]:
        target = self.sandbox.validate_path(path)
        if not target.exists():
            return {"error": f"File '{path}' does not exist."}
        if target.is_dir():
            return {"error": f"Path '{path}' is a directory, not a file."}

        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            selected = lines[offset : offset + limit]
            content = "".join(selected)

            return {
                "path": str(target.relative_to(self.sandbox.workspace_root)),
                "content": content,
                "total_lines": total_lines,
                "offset": offset,
                "limit": limit,
                "truncated": (offset + limit) < total_lines,
            }
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}


class WriteFileArgs(BaseModel):
    path: str = Field(description="Relative path to file inside workspace")
    content: str = Field(description="Full text content to write")
    overwrite: bool = Field(default=True, description="Whether to overwrite existing file")


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write or create a file within the workspace."
    risk_level = RiskLevel.MODIFICATION
    args_schema = WriteFileArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        target = self.sandbox.validate_path(path)
        if target.exists() and not overwrite:
            return {"error": f"File '{path}' already exists and overwrite is set to False."}

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "path": str(target.relative_to(self.sandbox.workspace_root)),
                "bytes_written": len(content.encode("utf-8")),
            }
        except Exception as e:
            return {"error": f"Failed to write file: {e}"}


class EditFileArgs(BaseModel):
    path: str = Field(description="Relative path to file inside workspace")
    target_text: str = Field(description="Exact substring to find and replace")
    replacement_text: str = Field(description="New substring to insert")


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Edit an existing file by replacing a unique substring."
    risk_level = RiskLevel.MODIFICATION
    args_schema = EditFileArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, path: str, target_text: str, replacement_text: str) -> Dict[str, Any]:
        target = self.sandbox.validate_path(path)
        if not target.exists():
            return {"error": f"File '{path}' does not exist."}

        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()

            if target_text not in content:
                return {"error": f"Target text not found in file '{path}'."}

            occurrences = content.count(target_text)
            if occurrences > 1:
                return {"error": f"Target text appears {occurrences} times. Must be unique to replace safely."}

            new_content = content.replace(target_text, replacement_text, 1)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {
                "success": True,
                "path": str(target.relative_to(self.sandbox.workspace_root)),
                "message": "Replaced target text successfully.",
            }
        except Exception as e:
            return {"error": f"Failed to edit file: {e}"}


class ListDirectoryArgs(BaseModel):
    path: str = Field(default=".", description="Relative directory path (default: root)")
    recursive: bool = Field(default=False, description="List recursively")
    max_entries: int = Field(default=100, description="Max entries to return")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and folders in a workspace directory."
    risk_level = RiskLevel.SAFE
    args_schema = ListDirectoryArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, path: str = ".", recursive: bool = False, max_entries: int = 100) -> Dict[str, Any]:
        target = self.sandbox.validate_path(path)
        if not target.exists():
            return {"error": f"Directory '{path}' does not exist."}
        if not target.is_dir():
            return {"error": f"Path '{path}' is not a directory."}

        entries = []
        try:
            if recursive:
                for root, dirs, files in os.walk(target):
                    # Filter out git/venv
                    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
                    rel_root = Path(root).relative_to(self.sandbox.workspace_root)
                    for d in dirs:
                        entries.append({"name": str(rel_root / d), "type": "directory"})
                        if len(entries) >= max_entries:
                            break
                    for f in files:
                        entries.append({"name": str(rel_root / f), "type": "file"})
                        if len(entries) >= max_entries:
                            break
                    if len(entries) >= max_entries:
                        break
            else:
                for item in sorted(target.iterdir()):
                    if item.name.startswith(".") and item.name not in (".proton", ".gitignore"):
                        continue
                    entries.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    })
                    if len(entries) >= max_entries:
                        break

            return {
                "path": str(target.relative_to(self.sandbox.workspace_root)),
                "entries": entries,
                "count": len(entries),
            }
        except Exception as e:
            return {"error": f"Failed to list directory: {e}"}


class SearchCodeArgs(BaseModel):
    query: str = Field(description="Text or regex search pattern")
    path: str = Field(default=".", description="Subdirectory to search inside")
    is_regex: bool = Field(default=False, description="Treat query as regular expression")
    max_results: int = Field(default=30, description="Max matching lines to return")


class SearchCodeTool(BaseTool):
    name = "search_code"
    description = "Search for strings or patterns in repository files."
    risk_level = RiskLevel.SAFE
    args_schema = SearchCodeArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, query: str, path: str = ".", is_regex: bool = False, max_results: int = 30) -> Dict[str, Any]:
        target = self.sandbox.validate_path(path)
        pattern = re.compile(query if is_regex else re.escape(query), re.IGNORECASE)
        results = []

        ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
        ignore_exts = {".png", ".jpg", ".jpeg", ".exe", ".dll", ".so", ".pyc", ".lock"}

        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in ignore_exts:
                    continue
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append({
                                    "file": str(file_path.relative_to(self.sandbox.workspace_root)),
                                    "line": line_no,
                                    "content": line.strip()[:200],
                                })
                                if len(results) >= max_results:
                                    break
                except Exception:
                    continue
                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        return {"query": query, "matches": results, "count": len(results)}
