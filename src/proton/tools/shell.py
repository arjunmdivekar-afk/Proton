"""Shell command executor with timeouts, security, and output capture."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.security.sandbox import FilesystemSandbox


class ShellExecuteArgs(BaseModel):
    command: str = Field(description="Shell command line to execute")
    cwd: Optional[str] = Field(default=None, description="Working directory relative to workspace")
    timeout_seconds: float = Field(default=60.0, description="Max execution duration before timeout")


class ShellExecuteTool(BaseTool):
    name = "shell_execute"
    description = "Execute a shell command inside the workspace with timeout protection."
    risk_level = RiskLevel.EXECUTION
    args_schema = ShellExecuteArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, command: str, cwd: Optional[str] = None, timeout_seconds: float = 60.0) -> Dict[str, Any]:
        target_cwd = self.sandbox.validate_path(cwd or ".")
        if not target_cwd.exists() or not target_cwd.is_dir():
            return {"error": f"Working directory '{cwd}' does not exist."}

        # Use appropriate shell per OS
        is_win = sys.platform == "win32"
        shell_cmd = command

        try:
            process = await asyncio.create_subprocess_shell(
                shell_cmd,
                cwd=str(target_cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return {
                    "success": False,
                    "exit_code": -1,
                    "error": f"Command execution timed out after {timeout_seconds} seconds.",
                    "command": command,
                }

            stdout_str = stdout_bytes.decode("utf-8", errors="replace")
            stderr_str = stderr_bytes.decode("utf-8", errors="replace")

            # Truncate overly long output to keep context clean
            max_chars = 10000
            truncated = False
            if len(stdout_str) > max_chars:
                stdout_str = stdout_str[:max_chars] + f"\n... [Output truncated. Total characters: {len(stdout_bytes)}]"
                truncated = True

            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "truncated": truncated,
                "command": command,
            }
        except Exception as e:
            return {"error": f"Failed to execute shell process: {e}"}
