"""Project Knowledge Graph & GraphRAG API routes with Python client examples."""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from proton.server.schemas import GraphImpactResponse, GraphStatsResponse
from proton.graph.engine import ProjectGraphEngine

router = APIRouter(prefix="/v1/graph", tags=["Project Knowledge Graph"])


@router.get(
    "/impact",
    summary="Calculate Change Impact & Blast Radius",
    response_model=GraphImpactResponse,
)
async def get_impact(symbol: str, workspace: Optional[str] = None):
    """
    Perform Change Impact Analysis ("What will break if I change this function or class?").

    Traverses AST static call and inheritance chains to discover direct callers, indirect callers,
    importing modules, and affected unit test suites.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/graph/impact"
    params = {"symbol": "validate_path"}

    response = requests.get(url, params=params)
    data = response.json()
    print(f"Target: {data['symbol']}")
    print(f"Blast Radius Score: {data['total_blast_radius']}")
    print("Direct Callers:", data["direct_callers"])
    print("Tests Affected:", data["tests_affected"])
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    report = engine.impact_analysis(symbol)
    if not report:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in project knowledge graph.")

    return GraphImpactResponse(
        symbol=report.target_symbol,
        direct_callers=report.direct_callers,
        indirect_callers=report.indirect_callers,
        tests_affected=report.affecting_tests,
        modules_impacted=report.importing_modules,
        total_blast_radius=report.total_blast_radius,
    )


@router.get(
    "/callers",
    summary="Discover Symbol Callers",
)
async def get_callers(symbol: str, workspace: Optional[str] = None):
    """
    Find all functions and modules that call a given symbol.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/graph/callers"
    response = requests.get(url, params={"symbol": "validate_path"})
    print("Callers:", response.json())
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    nodes = engine.get_incoming_calls(symbol)
    return {
        "symbol": symbol,
        "callers": [{"name": n.name, "file": n.file_path, "line": n.line_number} for n in nodes],
        "total": len(nodes),
    }


@router.get(
    "/tests",
    summary="Discover Tests Covering Symbol",
)
async def get_tests(symbol: str, workspace: Optional[str] = None):
    """
    Discover all automated test functions that execute or test a given symbol.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/graph/tests"
    response = requests.get(url, params={"symbol": "validate_path"})
    print("Covering Tests:", response.json()["tests"])
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    tests = engine.get_tests_for_symbol(symbol)
    return {
        "symbol": symbol,
        "tests": [{"name": t.name, "file": t.file_path, "line": t.line_number} for t in tests],
        "total": len(tests),
    }


@router.get(
    "/stats",
    summary="Graph Node & Edge Statistics",
    response_model=GraphStatsResponse,
)
@router.get(
    "/structure",
    include_in_schema=False,
)
async def get_stats(workspace: Optional[str] = None):
    """
    Retrieve AST graph density, total nodes, relationships, functions, classes, and test counts.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/graph/stats"
    response = requests.get(url)
    stats = response.json()
    print(f"Total Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
    print(f"Functions: {stats['functions']}, Classes: {stats['classes']}")
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    stats = engine.get_stats()
    return GraphStatsResponse(
        total_nodes=stats.total_nodes,
        total_edges=stats.total_edges,
        functions=stats.functions_count,
        classes=stats.classes_count,
        modules=stats.modules_count,
        tests=stats.tests_count,
    )


@router.post(
    "/build",
    summary="Rebuild Knowledge Graph",
)
async def build_graph(workspace: Optional[str] = None):
    """
    Scan codebase files and rebuild AST structural knowledge graph in SQLite.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/graph/build"
    response = requests.post(url)
    print("Rebuilt Graph:", response.json())
    ```
    """
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    stats = engine.build_graph()
    return {
        "status": "success",
        "nodes_indexed": stats.total_nodes,
        "edges_indexed": stats.total_edges,
    }
