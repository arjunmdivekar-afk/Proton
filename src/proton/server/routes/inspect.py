"""Repository & Codebase Inspection API routes with Python client examples."""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter

from proton.inspect.analyzer import RepoAnalyzer

router = APIRouter(prefix="/v1/inspect", tags=["Inspection"])


@router.get(
    "",
    summary="Full Deep Repository Inspection",
)
async def inspect_repository(workspace: Optional[str] = None):
    """
    Run comprehensive structural inspection across languages, frameworks, architecture, dependencies, git status, tests, and security.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/inspect"
    response = requests.get(url)
    report = response.json()
    print("Project Name:", report["project_name"])
    print("Architecture Pattern:", report["architecture"]["pattern"])
    print("Dependencies Total:", report["dependencies"]["total_count"])
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    report = analyzer.analyze_all()
    return report.model_dump(mode="json")


@router.get(
    "/security",
    summary="Inspect Security & CVEs",
)
async def inspect_security(workspace: Optional[str] = None):
    """
    Run repository static security audit (hardcoded secrets, risky patterns, permissions).

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/inspect/security"
    response = requests.get(url)
    sec = response.json()
    print(f"Security Score: {sec['score']} / 100")
    print(f"Vulnerabilities Found: {len(sec['vulnerabilities'])}")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    sec = analyzer.audit_security()
    return sec.model_dump(mode="json")


@router.get(
    "/architecture",
    summary="Inspect Architecture & Layers",
)
async def inspect_architecture(workspace: Optional[str] = None):
    """
    Analyze architectural design patterns, structural layers, and execution entry points.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/inspect/architecture"
    response = requests.get(url)
    arch = response.json()
    print(f"Pattern: {arch['pattern']}")
    print(f"Layers: {arch['layers']}")
    print(f"Entry Points: {arch['entry_points']}")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    arch = analyzer.inspect_architecture()
    return arch.model_dump(mode="json")


@router.get(
    "/dependencies",
    summary="Inspect Dependencies & Package Managers",
)
async def inspect_dependencies(workspace: Optional[str] = None):
    """
    Analyze package manager manifests and direct dependencies.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/inspect/dependencies"
    response = requests.get(url)
    deps = response.json()
    print(f"Package Manager: {deps['package_manager']}")
    for d in deps["direct_dependencies"][:5]:
        print(f"- {d['name']} ({d['version_spec']})")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    deps = analyzer.inspect_dependencies()
    return deps.model_dump(mode="json")


@router.get(
    "/tests",
    summary="Inspect Test Suites",
)
async def inspect_tests(workspace: Optional[str] = None):
    """
    Discover test frameworks, test files, and test coverage configurations.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/inspect/tests"
    response = requests.get(url)
    tests = response.json()
    print(f"Framework: {tests['framework']}")
    print(f"Test Files: {tests['test_files_count']}")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    tests = analyzer.inspect_tests()
    return tests.model_dump(mode="json")


@router.get(
    "/performance",
    summary="Inspect Large Files & Disk Footprint",
)
async def inspect_performance(workspace: Optional[str] = None):
    """
    Detect large binary files (> 500 KB) and calculate total repository disk footprint.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/inspect/performance"
    response = requests.get(url)
    perf = response.json()
    print(f"Repo Size: {perf['total_repo_size_mb']} MB")
    print(f"Large Files: {len(perf['large_files'])}")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    analyzer = RepoAnalyzer(ws)
    perf = analyzer.inspect_performance()
    return perf.model_dump(mode="json")
