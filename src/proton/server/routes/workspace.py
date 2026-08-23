"""Workspace file explorer, editor, search, and diff APIs for Proton Web UI."""

import os
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

from proton.core.config import ConfigManager
from proton.security.sandbox import FilesystemSandbox

router = APIRouter(prefix="/v1/workspace", tags=["Workspace"])

# Track changes made in the session
_SESSION_CHANGES: List[Dict[str, Any]] = []


class FileWriteRequest(BaseModel):
    path: str
    content: str


class SearchRequest(BaseModel):
    query: str
    case_sensitive: bool = False
    max_results: int = 50


class DiffRequest(BaseModel):
    path: str
    modified_content: str


def get_sandbox() -> FilesystemSandbox:
    config_mgr = ConfigManager()
    ws_root = getattr(config_mgr.config, "workspace_dir", None)
    return FilesystemSandbox(workspace_root=Path(ws_root) if ws_root else Path.cwd())


@router.get("/tree")
async def get_workspace_tree(max_depth: int = Query(4, ge=1, le=10)) -> Dict[str, Any]:
    """Return recursive directory tree for the workspace explorer."""
    sandbox = get_sandbox()
    root = sandbox.workspace_root

    ignore_dirs = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".idea", ".vscode", "dist", "build"}

    def build_tree(current_path: Path, depth: int) -> Dict[str, Any]:
        node: Dict[str, Any] = {
            "name": current_path.name or str(current_path),
            "path": str(current_path.relative_to(root)).replace("\\", "/") if current_path != root else "",
            "is_dir": current_path.is_dir(),
            "size": 0,
        }

        if current_path.is_dir():
            children = []
            if depth < max_depth:
                try:
                    entries = sorted(current_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
                    for entry in entries:
                        if entry.name in ignore_dirs or (entry.name.startswith(".") and len(entry.name) > 1 and entry.name != ".env"):
                            continue
                        children.append(build_tree(entry, depth + 1))
                except PermissionError:
                    pass
            node["children"] = children
        else:
            try:
                node["size"] = current_path.stat().st_size
                node["extension"] = current_path.suffix.lower()
            except Exception:
                node["size"] = 0
                node["extension"] = ""

        return node

    return {
        "workspace_root": str(root),
        "tree": build_tree(root, 0),
    }


@router.get("/file")
async def read_workspace_file(path: str = Query(..., description="Relative file path")) -> Dict[str, Any]:
    """Read full file contents with line counts and metadata."""
    sandbox = get_sandbox()
    target = sandbox.validate_path(path)

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File '{path}' does not exist.")
    if target.is_dir():
        raise HTTPException(status_code=400, detail=f"Path '{path}' is a directory.")

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        stat = target.stat()
        return {
            "path": str(target.relative_to(sandbox.workspace_root)).replace("\\", "/"),
            "content": content,
            "size_bytes": stat.st_size,
            "total_lines": content.count("\n") + (1 if content else 0),
            "extension": target.suffix.lower(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")


@router.post("/file")
async def write_workspace_file(req: FileWriteRequest) -> Dict[str, Any]:
    """Write or overwrite file in workspace and track in session changes."""
    sandbox = get_sandbox()
    target = sandbox.validate_path(req.path)

    # Read previous content if exists for change tracking
    previous_content = ""
    is_new = not target.exists()
    if target.exists() and not target.is_dir():
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                previous_content = f.read()
        except Exception:
            pass

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(req.content)

    rel_path = str(target.relative_to(sandbox.workspace_root)).replace("\\", "/")
    _SESSION_CHANGES.append({
        "path": rel_path,
        "action": "created" if is_new else "modified",
        "previous_content": previous_content,
        "new_content": req.content,
        "timestamp": os.path.getmtime(target),
    })

    return {
        "success": True,
        "path": rel_path,
        "bytes_written": len(req.content.encode("utf-8")),
    }


@router.post("/search")
async def search_workspace_files(req: SearchRequest) -> Dict[str, Any]:
    """Search for text across workspace files."""
    sandbox = get_sandbox()
    root = sandbox.workspace_root
    results = []

    ignore_dirs = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", "dist", "build"}
    query = req.query if req.case_sensitive else req.query.lower()

    for root_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
        for file in files:
            if file.startswith(".") or file.endswith((".pyc", ".png", ".jpg", ".webp", ".zip", ".tar", ".gz", ".exe", ".dll", ".so")):
                continue

            file_path = Path(root_dir) / file
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        search_target = line if req.case_sensitive else line.lower()
                        if query in search_target:
                            results.append({
                                "file": str(file_path.relative_to(root)).replace("\\", "/"),
                                "line_number": line_num,
                                "line_content": line.strip(),
                            })
                            if len(results) >= req.max_results:
                                return {"results": results, "total": len(results), "truncated": True}
            except Exception:
                continue

    return {"results": results, "total": len(results), "truncated": False}


@router.post("/diff")
async def get_file_diff(req: DiffRequest) -> Dict[str, Any]:
    """Generate unified diff between on-disk file and modified content."""
    sandbox = get_sandbox()
    target = sandbox.validate_path(req.path)

    orig_content = ""
    if target.exists() and not target.is_dir():
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                orig_content = f.read()
        except Exception:
            pass

    orig_lines = orig_content.splitlines(keepends=True)
    mod_lines = req.modified_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{req.path}",
        tofile=f"b/{req.path}",
        lineterm="",
    ))

    return {
        "path": req.path,
        "diff_lines": diff,
        "diff_text": "\n".join(diff),
        "has_changes": len(diff) > 0,
    }


@router.get("/agent-changes")
async def get_agent_changes() -> Dict[str, Any]:
    """Return all files modified during the current server session."""
    return {"changes": _SESSION_CHANGES}
