"""Security Verification API routes with Python client examples."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter

from proton.server.schemas import SecurityVerificationResponse, SecurityCheckResponse
from proton.security.tester import SecurityTester
from proton.inspect.analyzer import RepoAnalyzer
from proton.core.config import ConfigManager

router = APIRouter(prefix="/v1/security", tags=["Security & Governance"])


@router.get(
    "",
    summary="Get Security Posture & Guardrails",
)
async def get_security_posture():
    """
    Get active approval policy, workspace isolation boundary, and command blacklist.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/security"
    response = requests.get(url)
    print("Security Posture:", response.json())
    ```
    """
    config_mgr = ConfigManager()
    cfg = config_mgr.config.security
    workspace = Path.cwd().resolve()
    return {
        "approval_policy": cfg.approval_policy.value,
        "workspace_root": str(workspace),
        "sandbox_active": True,
        "secret_redaction": cfg.redact_secrets,
        "blocked_commands_count": len(cfg.blocked_commands),
        "blocked_commands": cfg.blocked_commands,
        "allowed_commands": cfg.allowed_commands,
    }


@router.post(
    "/test",
    summary="Run Automated Defense Verification Battery",
    response_model=SecurityVerificationResponse,
)
async def run_security_tests(workspace: Optional[str] = None):
    """
    Run automated defensive verification battery across 8 threat vectors:
    - Path Traversal & Escapes
    - Workspace Containment
    - Command Injection & Chaining
    - Dangerous Shell Blacklist
    - Secret Token Redaction
    - Malicious Tool Argument Grader
    - Prompt Injection Heuristics
    - Unauthorized Network Boundaries

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/security/test"
    response = requests.post(url)
    data = response.json()
    print(f"Score: {data['security_score']} / 100 - {data['verdict']}")
    for check in data["checks"]:
        status = "PASS ✓" if check["passed"] else "FAIL ✗"
        print(f"- [{status}] {check['name']}: {check['risk_mitigated']}")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    tester = SecurityTester(ws)
    rep = tester.run_all_tests()

    return SecurityVerificationResponse(
        timestamp=rep.timestamp,
        workspace=rep.workspace,
        total_checks=rep.total_checks,
        passed_checks=rep.passed_checks,
        failed_checks=rep.failed_checks,
        security_score=rep.security_score,
        verdict=rep.verdict,
        checks=[
            SecurityCheckResponse(
                name=c.name,
                category=c.category,
                passed=c.passed,
                risk_mitigated=c.risk_mitigated,
                defense_layer=c.defense_layer,
                details=c.details,
            )
            for c in rep.checks
        ],
    )


@router.get(
    "/audit",
    summary="Workspace Static Security Audit",
)
async def run_security_audit(workspace: Optional[str] = None):
    """
    Scan workspace files for hardcoded secrets, dangerous patterns, and CVEs.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/security/audit"
    response = requests.get(url)
    print("Static Audit:", response.json())
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    sec = analyzer.audit_security()
    return sec.model_dump(mode="json")
