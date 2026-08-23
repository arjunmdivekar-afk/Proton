"""Security Verification API routes."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter

from proton.server.schemas import SecurityVerificationResponse, SecurityCheckResponse
from proton.security.tester import SecurityTester
from proton.inspect.analyzer import RepoAnalyzer
from proton.core.config import ConfigManager

router = APIRouter(prefix="/v1/security", tags=["Security & Governance"])


@router.get("")
async def get_security_posture():
    """Get active security configuration, approval policy, and sandboxing rules."""
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


@router.post("/test", response_model=SecurityVerificationResponse)
async def run_security_tests(workspace: Optional[str] = None):
    """Run automated defense verification battery against 8 threat vectors."""
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


@router.get("/audit")
async def run_security_audit(workspace: Optional[str] = None):
    """Scan workspace for exposed API keys, dangerous code patterns, and CVEs."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    sec = analyzer.audit_security()
    return sec.model_dump(mode="json")
