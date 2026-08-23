"""Autonomous Agent API routes."""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from proton.server.schemas import AgentRunRequest, AgentRunResponse
from proton.agent.max_agent import ProtonMaxAgent

router = APIRouter(prefix="/v1/agents", tags=["Autonomous Agent"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(req: AgentRunRequest):
    """Launch the Proton Max-Level Autonomous Agent on a goal with 10-stage lifecycle."""
    ws = Path(req.workspace).resolve() if req.workspace else Path.cwd()
    agent = ProtonMaxAgent(
        workspace_path=ws,
        auto_approve=req.auto_approve,
        max_steps=req.max_steps,
    )

    try:
        report = await agent.run(req.goal)
        return AgentRunResponse(
            goal=report.goal,
            status=report.status,
            plan=report.plan,
            steps_executed=report.steps_executed,
            files_modified=report.files_modified,
            commands_executed=report.commands_executed,
            tests_passed=report.tests_passed,
            audit_report_path=str(report.audit_report_path) if report.audit_report_path else None,
            summary=report.summary,
            duration_seconds=report.duration_seconds,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
