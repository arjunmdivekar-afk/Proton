"""Repository & Codebase Inspection API routes."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter

from proton.inspect.analyzer import RepoAnalyzer

router = APIRouter(prefix="/v1/inspect", tags=["Inspection"])


@router.get("")
async def inspect_repository(workspace: Optional[str] = None):
    """Run full deep structural inspection of the target repository."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    report = analyzer.analyze_all()
    return report.model_dump(mode="json")


@router.get("/security")
async def inspect_security(workspace: Optional[str] = None):
    """Run repository security audit (exposed keys, CVE patterns, and permissions)."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    sec = analyzer.audit_security()
    return sec.model_dump(mode="json")


@router.get("/architecture")
async def inspect_architecture(workspace: Optional[str] = None):
    """Analyze architectural layers, design patterns, and entry points."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    arch = analyzer.inspect_architecture()
    return arch.model_dump(mode="json")


@router.get("/dependencies")
async def inspect_dependencies(workspace: Optional[str] = None):
    """Analyze package managers, direct dependencies, and lockfiles."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    deps = analyzer.inspect_dependencies()
    return deps.model_dump(mode="json")


@router.get("/tests")
async def inspect_tests(workspace: Optional[str] = None):
    """Discover test suites, frameworks, and coverage configuration."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    tests = analyzer.inspect_tests()
    return tests.model_dump(mode="json")


@router.get("/performance")
async def inspect_performance(workspace: Optional[str] = None):
    """Inspect repository size and detect large files (> 500 KB)."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    perf = analyzer.inspect_performance()
    return perf.model_dump(mode="json")
