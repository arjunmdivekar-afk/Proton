"""Interactive terminal and shell execution router for Proton Web UI."""

import asyncio
import os
import sys
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from proton.core.config import ConfigManager
from proton.security.audit import AuditLogger
from proton.security.sandbox import FilesystemSandbox

router = APIRouter(prefix="/v1/terminal", tags=["Terminal"])

_COMMAND_HISTORY: List[Dict[str, Any]] = []
_ACTIVE_PROCESS: Optional[asyncio.subprocess.Process] = None
_ACTIVE_PROCESS_LOCK = asyncio.Lock()


class TerminalRunRequest(BaseModel):
    command: str = Field(..., description="Shell command string")
    cwd: Optional[str] = Field(None, description="Working directory relative to workspace root")
    timeout_seconds: float = Field(60.0, description="Max execution timeout in seconds")


@router.post("/run")
async def run_terminal_command(req: TerminalRunRequest) -> Dict[str, Any]:
    """Execute a shell command with live stdout/stderr capture and audit logging."""
    global _ACTIVE_PROCESS

    config_mgr = ConfigManager()
    ws_root = getattr(config_mgr.config, "workspace_dir", None) or str(os.getcwd())
    sandbox = FilesystemSandbox(workspace_root=ws_root)

    target_cwd = sandbox.validate_path(req.cwd or ".")
    if not target_cwd.exists() or not target_cwd.is_dir():
        target_cwd = sandbox.workspace_root

    # Record command in audit logger
    audit_logger = AuditLogger()
    audit_logger.log(
        event_type="terminal_execution",
        tool_name="terminal",
        decision="allowed",
        details={"command": req.command},
    )

    t_start = time.time()
    try:
        async with _ACTIVE_PROCESS_LOCK:
            _ACTIVE_PROCESS = await asyncio.create_subprocess_shell(
                req.command,
                cwd=str(target_cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),
            )
            proc = _ACTIVE_PROCESS

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=req.timeout_seconds
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {req.timeout_seconds} seconds.",
                "duration_ms": round((time.time() - t_start) * 1000, 2),
                "cwd": str(target_cwd.relative_to(sandbox.workspace_root)) or ".",
                "command": req.command,
            }
        finally:
            async with _ACTIVE_PROCESS_LOCK:
                if _ACTIVE_PROCESS == proc:
                    _ACTIVE_PROCESS = None

        stdout_str = stdout_bytes.decode("utf-8", errors="replace")
        stderr_str = stderr_bytes.decode("utf-8", errors="replace")
        duration_ms = round((time.time() - t_start) * 1000, 2)

        entry = {
            "command": req.command,
            "exit_code": proc.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
            "cwd": str(target_cwd.relative_to(sandbox.workspace_root)) or ".",
        }
        _COMMAND_HISTORY.append(entry)

        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "duration_ms": duration_ms,
            "cwd": str(target_cwd.relative_to(sandbox.workspace_root)) or ".",
            "command": req.command,
        }

    except Exception as e:
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "duration_ms": round((time.time() - t_start) * 1000, 2),
            "cwd": str(target_cwd.relative_to(sandbox.workspace_root)) or ".",
            "command": req.command,
        }


@router.post("/stop")
async def stop_terminal_process() -> Dict[str, Any]:
    """Kill any actively running terminal subprocess."""
    global _ACTIVE_PROCESS
    async with _ACTIVE_PROCESS_LOCK:
        if _ACTIVE_PROCESS and _ACTIVE_PROCESS.returncode is None:
            try:
                _ACTIVE_PROCESS.kill()
                _ACTIVE_PROCESS = None
                return {"success": True, "message": "Process terminated."}
            except Exception as e:
                return {"success": False, "error": str(e)}
    return {"success": False, "message": "No active process running."}


@router.get("/history")
async def get_terminal_history() -> Dict[str, Any]:
    """Get list of executed terminal commands."""
    return {"history": _COMMAND_HISTORY[-100:]}


@router.get("/status")
async def get_terminal_status() -> Dict[str, Any]:
    """Check if a process is currently executing."""
    is_running = _ACTIVE_PROCESS is not None and _ACTIVE_PROCESS.returncode is None
    config_mgr = ConfigManager()
    ws_root = getattr(config_mgr.config, "workspace_dir", None) or str(os.getcwd())
    return {
        "is_running": is_running,
        "pid": _ACTIVE_PROCESS.pid if is_running else None,
        "workspace_root": ws_root,
    }
