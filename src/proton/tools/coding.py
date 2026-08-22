"""Coding & Patch tools (unified diff applicator, test runner)."""

import asyncio
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from proton.tools.base import BaseTool
from proton.core.types import RiskLevel
from proton.security.sandbox import FilesystemSandbox


class ApplyPatchArgs(BaseModel):
    file_path: str = Field(description="Relative path of file to patch")
    patch_diff: str = Field(description="Unified diff or chunk replacement")


class ApplyPatchTool(BaseTool):
    name = "apply_patch"
    description = "Apply a unified diff or patch to a specific file."
    risk_level = RiskLevel.MODIFICATION
    args_schema = ApplyPatchArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, file_path: str, patch_diff: str) -> Dict[str, Any]:
        target = self.sandbox.validate_path(file_path)
        if not target.exists():
            return {"error": f"Target file '{file_path}' does not exist."}

        try:
            with open(target, "r", encoding="utf-8") as f:
                original_lines = f.readlines()

            # Parse simple unified diff format or line replacements
            patch_lines = patch_diff.strip().splitlines()
            cleaned_original = [line.rstrip("\r\n") for line in original_lines]

            # Attempt standard fuzzy matching or direct line substitution
            # If standard unified diff:
            removals = []
            additions = []
            for line in patch_lines:
                if line.startswith("-") and not line.startswith("---"):
                    removals.append(line[1:])
                elif line.startswith("+") and not line.startswith("+++"):
                    additions.append(line[1:])

            if removals:
                orig_text = "".join(original_lines)
                rem_text = "\n".join(removals)
                add_text = "\n".join(additions)
                if rem_text in orig_text:
                    new_text = orig_text.replace(rem_text, add_text, 1)
                    with open(target, "w", encoding="utf-8") as f:
                        f.write(new_text)
                    return {
                        "success": True,
                        "file": file_path,
                        "message": "Patch applied successfully via exact block substitution.",
                    }

            return {
                "error": "Could not cleanly apply patch. Please use edit_file or write_file for deterministic edits."
            }
        except Exception as e:
            return {"error": f"Failed to apply patch: {e}"}


class RunTestsArgs(BaseModel):
    test_path: Optional[str] = Field(default=None, description="Specific test file or folder")
    framework: Optional[str] = Field(default=None, description="Test framework override (pytest, npm, cargo)")


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Auto-detect and run workspace test suite (pytest, npm test, cargo test, go test)."
    risk_level = RiskLevel.EXECUTION
    args_schema = RunTestsArgs

    def __init__(self, sandbox: FilesystemSandbox) -> None:
        self.sandbox = sandbox

    async def run(self, test_path: Optional[str] = None, framework: Optional[str] = None) -> Dict[str, Any]:
        root = self.sandbox.workspace_root

        # Auto-detect test runner if not specified
        cmd: List[str] = []
        if framework == "pytest" or (root / "pytest.ini").exists() or (root / "tests").exists():
            cmd = ["pytest"]
            if test_path:
                cmd.append(test_path)
            cmd.append("-v")
        elif framework == "npm" or (root / "package.json").exists():
            cmd = ["npm", "test"]
        elif framework == "cargo" or (root / "Cargo.toml").exists():
            cmd = ["cargo", "test"]
        elif framework == "go" or (root / "go.mod").exists():
            cmd = ["go", "test", "./..."]
        else:
            # Fallback to python unittest
            cmd = ["python", "-m", "unittest", "discover"]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            passed = proc.returncode == 0
            return {
                "command": " ".join(cmd),
                "passed": passed,
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", "replace")[:5000],
                "stderr": stderr.decode("utf-8", "replace")[:5000],
            }
        except Exception as e:
            return {"error": f"Failed to run test command '{' '.join(cmd)}': {e}"}
