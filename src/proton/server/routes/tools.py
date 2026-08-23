"""Deterministic Tools API routes."""

import time
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from proton.server.schemas import ToolInfo, ToolExecuteRequest, ToolExecuteResponse
from proton.tools.registry import ToolRegistry
from proton.security.sandbox import FilesystemSandbox
from proton.security.policy import PolicyEngine
from proton.security.approval import ApprovalManager
from proton.core.types import ApprovalPolicy, ApprovalDecision
from proton.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirectoryTool, SearchCodeTool
from proton.tools.shell import ShellExecuteTool
from proton.tools.git import GitStatusTool, GitDiffTool, GitLogTool, GitCommitTool
from proton.tools.web_search import DuckDuckGoSearchTool, FetchWebPageTool

router = APIRouter(prefix="/v1/tools", tags=["Deterministic Tools"])


def _get_registry(workspace_path: Optional[Path] = None) -> ToolRegistry:
    ws = (workspace_path or Path.cwd()).resolve()
    sandbox = FilesystemSandbox(ws)
    policy = PolicyEngine()
    approval = ApprovalManager(ApprovalPolicy.AUTONOMOUS)
    approval.set_custom_handler(lambda tool, args, risk: ApprovalDecision.ALLOW_ONCE)

    reg = ToolRegistry(policy_engine=policy, approval_manager=approval)
    reg.register(ReadFileTool(sandbox))
    reg.register(WriteFileTool(sandbox))
    reg.register(EditFileTool(sandbox))
    reg.register(ListDirectoryTool(sandbox))
    reg.register(SearchCodeTool(sandbox))
    reg.register(ShellExecuteTool(sandbox))
    reg.register(GitStatusTool(sandbox))
    reg.register(GitDiffTool(sandbox))
    reg.register(GitLogTool(sandbox))
    reg.register(GitCommitTool(sandbox))
    reg.register(DuckDuckGoSearchTool())
    reg.register(FetchWebPageTool())
    return reg


@router.get("", response_model=List[ToolInfo])
async def list_tools():
    """List all registered tools, risk ratings, and JSON schemas."""
    reg = _get_registry()
    tools = reg.list_tools()
    return [
        ToolInfo(
            name=t.name,
            description=t.description,
            parameters=t.get_json_schema().get("function", {}).get("parameters", {}),
            risk_level=t.risk_level.value if hasattr(t.risk_level, "value") else str(t.risk_level),
        )
        for t in tools
    ]


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(req: ToolExecuteRequest):
    """Securely execute a tool within the sandbox with policy checks."""
    ws = Path(req.workspace).resolve() if req.workspace else Path.cwd()
    reg = _get_registry(ws)

    tool = reg.get_tool(req.tool)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{req.tool}' not found.")

    start = time.perf_counter()
    res = await reg.execute(req.tool, req.arguments)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    return ToolExecuteResponse(
        tool=req.tool,
        success=res.success,
        result=res.data if res.success else None,
        error=res.error if not res.success else None,
        duration_ms=duration_ms,
    )
