"""Git integration tools for Proton."""

import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.security.sandbox import FilesystemSandbox


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Get current git branch, tracked, untracked, and modified files."
    risk_level = RiskLevel.SAFE

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain", "-b",
            cwd=str(self.sandbox.workspace_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {"error": stderr.decode("utf-8", "replace")}

        lines = stdout.decode("utf-8", "replace").splitlines()
        branch = lines[0] if lines else "unknown"
        changes = lines[1:] if len(lines) > 1 else []
        return {
            "branch": branch,
            "changed_files": changes,
            "total_changes": len(changes),
        }


class GitDiffArgs(BaseModel):
    cached: bool = Field(default=False, description="Show staged changes only")
    file_path: Optional[str] = Field(default=None, description="Limit diff to a specific file")


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "View unified git diff of unstaged or staged modifications."
    risk_level = RiskLevel.SAFE
    args_schema = GitDiffArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, cached: bool = False, file_path: Optional[str] = None) -> Dict[str, Any]:
        cmd = ["git", "diff"]
        if cached:
            cmd.append("--cached")
        if file_path:
            cmd.extend(["--", file_path])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.sandbox.workspace_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {"error": stderr.decode("utf-8", "replace")}

        diff_str = stdout.decode("utf-8", "replace")
        return {
            "diff": diff_str,
            "has_changes": bool(diff_str.strip()),
        }


class GitLogArgs(BaseModel):
    max_count: int = Field(default=10, description="Max commits to display")


class GitLogTool(BaseTool):
    name = "git_log"
    description = "Get recent git commit history."
    risk_level = RiskLevel.SAFE
    args_schema = GitLogArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, max_count: int = 10) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "git", "log", f"-n{max_count}", "--oneline",
            cwd=str(self.sandbox.workspace_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {"error": stderr.decode("utf-8", "replace")}

        commits = [line.strip() for line in stdout.decode("utf-8", "replace").splitlines() if line.strip()]
        return {"commits": commits, "count": len(commits)}


class GitCommitArgs(BaseModel):
    message: str = Field(description="Commit message")
    add_all: bool = Field(default=True, description="Stage all modified files before committing")


class GitCommitTool(BaseTool):
    name = "git_commit"
    description = "Stage and commit changes to the git repository."
    risk_level = RiskLevel.MODIFICATION
    args_schema = GitCommitArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, message: str, add_all: bool = True) -> Dict[str, Any]:
        if add_all:
            p_add = await asyncio.create_subprocess_exec(
                "git", "add", "-A",
                cwd=str(self.sandbox.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await p_add.communicate()

        proc = await asyncio.create_subprocess_exec(
            "git", "commit", "-m", message,
            cwd=str(self.sandbox.workspace_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {"error": stderr.decode("utf-8", "replace")}

        return {"success": True, "output": stdout.decode("utf-8", "replace")}
