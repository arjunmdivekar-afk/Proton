"""Comprehensive Repository & Codebase Analysis Engine for Proton."""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from proton.inspect.models import (
    FullInspectionReport,
    LanguageInfo,
    FrameworkInfo,
    DependencyReport,
    DependencyItem,
    ArchitectureReport,
    SecurityAuditReport,
    TestAuditReport,
    PerformanceReport,
    ProblemItem,
)

IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules", "dist", "build",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "target", ".idea", ".vscode",
    ".gemini", ".next", ".nuxt", "coverage", ".turbo", "egg-info"
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".rs": "Rust",
    ".go": "Go",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".java": "Java",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell Script",
    ".ps1": "PowerShell",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".md": "Markdown",
}


class RepoAnalyzer:
    """Performs deep static and structural analysis across any repository workspace."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace = (workspace_root or Path.cwd()).resolve()

    def inspect_all(self) -> FullInspectionReport:
        """Run full end-to-end repository inspection."""
        langs = self.detect_languages()
        frameworks = self.detect_frameworks()
        deps = self.inspect_dependencies()
        arch = self.inspect_architecture()
        entry_points = self.detect_entry_points()
        tests = self.inspect_tests()
        git_stat = self.inspect_git_status()
        docs = self.inspect_documentation()
        env = self.inspect_environment()
        problems = self.detect_problems(git_stat, tests, docs)
        sec = self.audit_security()
        perf = self.audit_performance()

        return FullInspectionReport(
            project_name=self.workspace.name,
            workspace_root=str(self.workspace),
            languages=langs,
            frameworks=frameworks,
            dependencies=deps,
            architecture=arch,
            entry_points=entry_points,
            test_framework=tests,
            git_status=git_stat,
            documentation=docs,
            environment=env,
            potential_problems=problems,
            security=sec,
            performance=perf,
        )

    def detect_languages(self) -> List[LanguageInfo]:
        """Scan codebase files and calculate line of code distribution."""
        lang_counts: Dict[str, Dict[str, int]] = {}

        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.endswith(".egg-info")]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in LANGUAGE_EXTENSIONS:
                    lang = LANGUAGE_EXTENSIONS[ext]
                    if lang not in lang_counts:
                        lang_counts[lang] = {"files": 0, "lines": 0}
                    lang_counts[lang]["files"] += 1
                    try:
                        filepath = Path(root) / file
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            lines = sum(1 for _ in f)
                            lang_counts[lang]["lines"] += lines
                    except Exception:
                        pass

        total_lines = sum(data["lines"] for data in lang_counts.values()) or 1
        result: List[LanguageInfo] = []
        for lang, data in sorted(lang_counts.items(), key=lambda x: x[1]["lines"], reverse=True):
            pct = round((data["lines"] / total_lines) * 100, 1)
            result.append(
                LanguageInfo(
                    name=lang,
                    files_count=data["files"],
                    lines_of_code=data["lines"],
                    percentage=pct,
                )
            )
        return result

    def detect_frameworks(self) -> List[FrameworkInfo]:
        """Detect web, CLI, data, and testing frameworks from manifests and imports."""
        found: List[FrameworkInfo] = []
        manifests = [
            self.workspace / "pyproject.toml",
            self.workspace / "requirements.txt",
            self.workspace / "package.json",
            self.workspace / "Cargo.toml",
            self.workspace / "go.mod",
        ]

        text_content = ""
        for m in manifests:
            if m.exists():
                try:
                    text_content += m.read_text(encoding="utf-8", errors="ignore").lower() + "\n"
                except Exception:
                    pass

        # Framework detection heuristics
        rules = [
            ("Typer", "CLI Framework", ["typer"]),
            ("Rich", "Terminal UI & Styling", ["rich"]),
            ("FastAPI", "Web API Framework", ["fastapi"]),
            ("Flask", "Web Framework", ["flask"]),
            ("Django", "Web Framework", ["django"]),
            ("React", "Frontend Framework", ["react", "react-dom"]),
            ("Next.js", "Full-Stack Web Framework", ["next", "nextjs"]),
            ("Vue", "Frontend Framework", ["vue"]),
            ("Pytest", "Testing Framework", ["pytest"]),
            ("yfinance", "Financial Market Data", ["yfinance"]),
            ("httpx", "Async HTTP Client", ["httpx"]),
            ("Pydantic", "Data Validation & Models", ["pydantic"]),
            ("Prompt Toolkit", "Interactive Terminal UI", ["prompt_toolkit", "prompt-toolkit"]),
            ("PyTorch", "Deep Learning / AI", ["torch", "pytorch"]),
            ("TailwindCSS", "CSS Framework", ["tailwindcss", "tailwind"]),
        ]

        for name, category, tokens in rules:
            if any(t in text_content for t in tokens):
                found.append(FrameworkInfo(name=name, category=category))

        return found

    def inspect_dependencies(self) -> DependencyReport:
        """Parse package dependencies and manifest files."""
        report = DependencyReport()

        pyproject = self.workspace / "pyproject.toml"
        reqs = self.workspace / "requirements.txt"
        pkg_json = self.workspace / "package.json"
        cargo = self.workspace / "Cargo.toml"

        if pyproject.exists():
            report.package_manager = "pip / PEP 621 (pyproject.toml)"
            report.manifest_files.append("pyproject.toml")
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            # Parse dependencies list
            dep_matches = re.findall(r'["\']([a-zA-Z0-9_\-\.]+)(?:[><=~^!].*?)?["\']', content)
            for d in set(dep_matches):
                if not d.startswith("http") and not d.startswith(".") and len(d) > 1:
                    report.direct_dependencies.append(DependencyItem(name=d))

        elif reqs.exists():
            report.package_manager = "pip (requirements.txt)"
            report.manifest_files.append("requirements.txt")
            for line in reqs.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    name = re.split(r"[><=~^!]", line)[0].strip()
                    if name:
                        report.direct_dependencies.append(DependencyItem(name=name))

        elif pkg_json.exists():
            report.package_manager = "npm / yarn / pnpm"
            report.manifest_files.append("package.json")
            import json
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                for k, v in data.get("dependencies", {}).items():
                    report.direct_dependencies.append(DependencyItem(name=k, version_spec=str(v)))
                for k, v in data.get("devDependencies", {}).items():
                    report.direct_dependencies.append(DependencyItem(name=k, version_spec=str(v), is_dev=True))
            except Exception:
                pass

        elif cargo.exists():
            report.package_manager = "Cargo (Rust)"
            report.manifest_files.append("Cargo.toml")

        report.total_count = len(report.direct_dependencies)
        return report

    def inspect_architecture(self) -> ArchitectureReport:
        """Analyze project structural pattern and core layers."""
        layers: List[str] = []
        modules: List[str] = []

        src_dir = self.workspace / "src"
        search_root = src_dir if src_dir.exists() else self.workspace

        if search_root.exists() and search_root.is_dir():
            for item in search_root.iterdir():
                if item.is_dir() and item.name not in IGNORED_DIRS:
                    modules.append(item.name)

        if "cli" in modules and ("core" in modules or "agent" in modules):
            pattern = "Layered Enterprise CLI / Agent Architecture"
        elif "app" in modules or "pages" in modules or "routes" in modules:
            pattern = "Modular Web Application Architecture"
        elif "src" in [p.name for p in self.workspace.iterdir() if p.is_dir()]:
            pattern = "Standard Source Layout (`src/` package structure)"
        else:
            pattern = "Flat / Monolithic Repository"

        # Identify layers
        for l in ("cli", "agent", "browser", "stocks", "tasks", "rag", "security", "core", "tools", "tui", "providers"):
            if any(l in m for m in modules) or (self.workspace / "src" / "proton" / l).exists():
                layers.append(l)

        entry_points = self.detect_entry_points()
        return ArchitectureReport(
            pattern=pattern,
            entry_points=entry_points,
            core_modules=modules[:10],
            layers=layers,
        )

    def detect_entry_points(self) -> List[str]:
        """Detect execution entry points."""
        entries: List[str] = []
        candidates = [
            "src/proton/cli/app.py",
            "src/proton/main.py",
            "main.py",
            "app.py",
            "cli.py",
            "run.py",
            "src/index.ts",
            "src/index.js",
            "src/main.rs",
            "main.go",
        ]
        for c in candidates:
            if (self.workspace / c).exists():
                entries.append(c)

        # Check pyproject scripts
        pyproj = self.workspace / "pyproject.toml"
        if pyproj.exists():
            content = pyproj.read_text(encoding="utf-8", errors="ignore")
            if "[project.scripts]" in content:
                scripts = re.findall(r'([a-zA-Z0-9_\-]+)\s*=\s*["\']([^"\']+)["\']', content)
                for name, target in scripts:
                    entries.append(f"CLI Script: `{name}` -> `{target}`")

        return entries

    def inspect_tests(self) -> TestAuditReport:
        """Inspect automated test framework and test suites."""
        framework = "None detected"
        test_dirs: List[str] = []
        test_files_count = 0

        for candidate in ("tests", "test", "spec", "__tests__"):
            td = self.workspace / candidate
            if td.exists() and td.is_dir():
                test_dirs.append(candidate)
                for root, _, files in os.walk(td):
                    for f in files:
                        if f.startswith("test_") or f.endswith("_test.py") or f.endswith(".spec.ts") or f.endswith(".test.js"):
                            test_files_count += 1

        if (self.workspace / "pytest.ini").exists() or (self.workspace / "pyproject.toml").exists():
            framework = "Pytest"
        elif test_files_count > 0:
            framework = "Unit test suite"

        has_ci = (self.workspace / ".github" / "workflows").exists() or (self.workspace / ".gitlab-ci.yml").exists()
        return TestAuditReport(
            framework=framework,
            test_files_count=test_files_count,
            test_directories=test_dirs,
            has_ci_config=has_ci,
            estimated_coverage="Configured" if test_files_count > 0 else "Needs Tests",
        )

    def inspect_git_status(self) -> Dict[str, Any]:
        """Query repository Git branch and uncommitted files."""
        try:
            branch_p = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=3,
            )
            branch = branch_p.stdout.strip() or "main"

            status_p = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=3,
            )
            changed_lines = [l for l in status_p.stdout.splitlines() if l.strip()]

            commit_p = subprocess.run(
                ["git", "log", "-n", "1", "--oneline"],
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=3,
            )
            last_commit = commit_p.stdout.strip() or "No commits yet"

            return {
                "is_git_repo": True,
                "branch": branch,
                "uncommitted_files_count": len(changed_lines),
                "is_clean": len(changed_lines) == 0,
                "last_commit": last_commit,
            }
        except Exception:
            return {"is_git_repo": False, "branch": "unknown", "is_clean": True}

    def inspect_documentation(self) -> List[str]:
        """Find documentation files in repo."""
        docs: List[str] = []
        for name in ("README.md", "ARCHITECTURE.md", "SECURITY.md", "CONFIGURATION.md", "CONTRIBUTING.md", "LICENSE", "CHANGELOG.md"):
            if (self.workspace / name).exists():
                docs.append(name)
        docs_dir = self.workspace / "docs"
        if docs_dir.exists() and docs_dir.is_dir():
            docs.append("docs/ (Directory)")
        return docs

    def inspect_environment(self) -> Dict[str, Any]:
        """Inspect active runtime and environment setup."""
        return {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "has_virtualenv": hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
            "dockerfile": (self.workspace / "Dockerfile").exists(),
            "env_file": (self.workspace / ".env").exists(),
            "env_example": (self.workspace / ".env.example").exists(),
        }

    def detect_problems(self, git_stat: Dict[str, Any], tests: TestAuditReport, docs: List[str]) -> List[ProblemItem]:
        """Detect potential architectural, test, and repository hygiene problems."""
        problems: List[ProblemItem] = []

        if not (self.workspace / ".gitignore").exists():
            problems.append(
                ProblemItem(
                    severity="MEDIUM",
                    title="Missing .gitignore",
                    description="Repository does not have a .gitignore file, risking accidental secret/cache commits.",
                )
            )

        if tests.test_files_count == 0:
            problems.append(
                ProblemItem(
                    severity="LOW",
                    title="No Test Suite Found",
                    description="No automated test files detected. Consider creating a `tests/` directory.",
                )
            )

        if "README.md" not in docs:
            problems.append(
                ProblemItem(
                    severity="LOW",
                    title="Missing README.md",
                    description="No project README file found in root.",
                )
            )

        return problems

    def audit_security(self) -> SecurityAuditReport:
        """Scan for hardcoded secrets, dangerous functions, and security files."""
        sec_report = SecurityAuditReport()
        docs = self.inspect_documentation()
        sec_report.security_files = [d for d in docs if d in ("SECURITY.md", "LICENSE")]

        secret_patterns = [
            re.compile(r'(?i)(?:api_key|secret_key|private_key|token|auth_token)\s*=\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']'),
        ]

        found_secrets: List[str] = []
        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for f in files:
                if f.endswith((".py", ".js", ".ts", ".json", ".yaml", ".env")):
                    p = Path(root) / f
                    try:
                        text = p.read_text(encoding="utf-8", errors="ignore")
                        for pat in secret_patterns:
                            for m in pat.findall(text):
                                if "placeholder" not in m.lower() and "example" not in m.lower():
                                    rel = str(p.relative_to(self.workspace))
                                    found_secrets.append(f"{rel}: {m[:6]}***")
                    except Exception:
                        pass

        sec_report.hardcoded_secrets_found = found_secrets
        if found_secrets:
            sec_report.score = max(0, sec_report.score - 30)
            sec_report.vulnerabilities.append(
                ProblemItem(
                    severity="HIGH",
                    title="Hardcoded Secrets Detected",
                    description=f"Found {len(found_secrets)} potential exposed API keys or tokens.",
                )
            )

        return sec_report

    def audit_performance(self) -> PerformanceReport:
        """Identify oversized files and performance bottlenecks."""
        perf = PerformanceReport()
        large_files = []
        total_bytes = 0

        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for f in files:
                p = Path(root) / f
                try:
                    size = p.stat().st_size
                    total_bytes += size
                    if size > 1024 * 500:  # > 500 KB
                        rel = str(p.relative_to(self.workspace))
                        large_files.append({"path": rel, "size_kb": round(size / 1024, 1)})
                except Exception:
                    pass

        perf.total_repo_size_mb = round(total_bytes / (1024 * 1024), 2)
        perf.large_files = sorted(large_files, key=lambda x: x["size_kb"], reverse=True)[:10]
        return perf
