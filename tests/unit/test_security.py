"""Unit tests for Proton security, sandboxing, redaction, and policy."""

import pytest
from pathlib import Path
from proton.security.sandbox import FilesystemSandbox
from proton.security.redaction import redact_text, redact_data
from proton.security.policy import PolicyEngine
from proton.security.approval import ApprovalManager
from proton.core.types import RiskLevel, ApprovalDecision, ApprovalPolicy
from proton.core.exceptions import SecurityError, ApprovalDeniedError


def test_sandbox_path_validation(tmp_path: Path):
    sandbox = FilesystemSandbox(tmp_path)
    safe_file = sandbox.validate_path("src/app.py")
    assert safe_file == (tmp_path / "src" / "app.py").resolve()

    # Traversal attempt outside workspace
    with pytest.raises(SecurityError):
        sandbox.validate_path("../../outside.txt")


def test_secret_redaction():
    text = "Here is my secret sk-abcdef12345678901234567890 and Bearer eyJhbGciOiJIUzI1NiJ9.test"
    redacted = redact_text(text)
    assert "sk-" not in redacted or "***REDACTED" in redacted
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted

    data = {"api_key": "supersecret123", "normal": "hello"}
    redacted_data = redact_data(data)
    assert redacted_data["api_key"] == "***REDACTED***"
    assert redacted_data["normal"] == "hello"


def test_policy_engine_risk_levels():
    engine = PolicyEngine()
    risk, _ = engine.evaluate_command("rm -rf /")
    assert risk == RiskLevel.DESTRUCTIVE

    risk, _ = engine.evaluate_command("git status")
    assert risk == RiskLevel.SAFE

    risk, _ = engine.evaluate_command("pytest -v")
    assert risk == RiskLevel.EXECUTION


@pytest.mark.asyncio
async def test_approval_manager():
    mgr = ApprovalManager(policy=ApprovalPolicy.STRICT)

    # Deny handler
    mgr.set_custom_handler(lambda t, a, r: ApprovalDecision.DENY)
    with pytest.raises(ApprovalDeniedError):
        await mgr.request_approval("shell_execute", {"command": "ls"}, RiskLevel.EXECUTION)

    # Allow session handler
    mgr.set_custom_handler(lambda t, a, r: ApprovalDecision.ALLOW_SESSION)
    allowed = await mgr.request_approval("read_file", {"path": "a.txt"}, RiskLevel.SAFE)
    assert allowed is True

    # Subsequent call should automatically pass
    mgr.set_custom_handler(lambda t, a, r: ApprovalDecision.DENY)
    assert await mgr.request_approval("read_file", {"path": "a.txt"}, RiskLevel.SAFE) is True
