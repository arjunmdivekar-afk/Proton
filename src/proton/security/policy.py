"""Policy engine for command and tool authorization."""

import shlex
from typing import List, Optional, Tuple
from proton.core.types import RiskLevel, ApprovalPolicy
from proton.core.config import SecurityConfig
from proton.core.exceptions import SecurityError


class PolicyEngine:
    """Evaluates safety policies for tool invocations and shell commands."""

    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        self.config = config or SecurityConfig()

    def evaluate_command(self, command_line: str) -> Tuple[RiskLevel, Optional[str]]:
        """Classify shell command and detect blocked/dangerous commands."""
        clean = command_line.strip().lower()

        # Check explicitly blocked commands
        for blocked in self.config.blocked_commands:
            if blocked.lower() in clean:
                return RiskLevel.DESTRUCTIVE, f"Command contains explicitly blocked pattern: '{blocked}'"

        # Danger checks
        if any(w in clean for w in ("rm -rf", "del /f /s /q", "format ", "drop database", "git push --force")):
            return RiskLevel.DESTRUCTIVE, "Potentially destructive operation detected."

        if any(w in clean for w in ("git push", "npm publish", "docker push", "terraform apply")):
            return RiskLevel.DESTRUCTIVE, "Consequential external state change."

        if any(w in clean for w in ("git commit", "npm install", "pip install", "pytest", "python", "make")):
            return RiskLevel.EXECUTION, None

        return RiskLevel.SAFE, None

    def get_tool_risk(self, tool_name: str, arguments: dict) -> RiskLevel:
        """Determine risk level of a tool call."""
        safe_tools = {"read_file", "list_directory", "search_code", "file_info", "git_status", "git_diff", "git_log", "rag_search", "memory_search"}
        modification_tools = {"write_file", "edit_file", "create_file", "delete_file", "apply_patch", "git_commit", "memory_add", "memory_delete", "rag_index"}
        execution_tools = {"shell_execute", "run_tests"}

        if tool_name in safe_tools:
            return RiskLevel.SAFE
        elif tool_name in modification_tools:
            return RiskLevel.MODIFICATION
        elif tool_name in execution_tools:
            cmd = arguments.get("command", "")
            risk, _ = self.evaluate_command(cmd)
            return risk if risk == RiskLevel.DESTRUCTIVE else RiskLevel.EXECUTION
        return RiskLevel.MODIFICATION
