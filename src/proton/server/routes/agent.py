"""Autonomous Agent API routes with Python client examples."""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from proton.server.schemas import AgentRunRequest, AgentRunResponse
from proton.agent.max_agent import ProtonMaxAgent

router = APIRouter(prefix="/v1/agents", tags=["Autonomous Agent"])


@router.post(
    "/run",
    summary="Launch Max-Level Autonomous Agent",
    response_model=AgentRunResponse,
)
async def run_agent(req: AgentRunRequest):
    """
    Launch the Proton Max-Level Autonomous Agent on a high-level goal.

    Executes the complete 10-stage autonomous lifecycle:
    `Understand ➔ Inspect ➔ Plan ➔ Approve ➔ Tools ➔ Modify ➔ Test ➔ Review ➔ Self-Heal ➔ Report`

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/agents/run"
    payload = {
        "goal": "Refactor authentication module to support JWT validation and run tests",
        "auto_approve": True,
        "max_steps": 30
    }

    response = requests.post(url, json=payload, timeout=300.0)
    report = response.json()
    print("Agent Status:", report["status"])
    print("Files Modified:", report["files_modified"])
    print("Tests Passed:", report["tests_passed"])
    print("Audit Report:", report["audit_report_path"])
    ```
    """
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
