"""Project Knowledge Graph & GraphRAG API routes."""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from proton.server.schemas import GraphImpactResponse, GraphStatsResponse
from proton.graph.engine import ProjectGraphEngine

router = APIRouter(prefix="/v1/graph", tags=["Project Knowledge Graph"])


@router.get("/impact", response_model=GraphImpactResponse)
async def get_impact(symbol: str, workspace: Optional[str] = None):
    """Analyze Change Impact & Blast Radius ("What will break if I change this function?")."""
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


@router.get("/callers")
async def get_callers(symbol: str, workspace: Optional[str] = None):
    """Discover all functions and modules that call a given symbol."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    nodes = engine.get_incoming_calls(symbol)
    return {
        "symbol": symbol,
        "callers": [{"name": n.name, "file": n.file_path, "line": n.line_number} for n in nodes],
        "total": len(nodes),
    }


@router.get("/tests")
async def get_tests(symbol: str, workspace: Optional[str] = None):
    """Discover all automated unit tests covering a given symbol."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    tests = engine.get_tests_for_symbol(symbol)
    return {
        "symbol": symbol,
        "tests": [{"name": t.name, "file": t.file_path, "line": t.line_number} for t in tests],
        "total": len(tests),
    }


@router.get("/stats", response_model=GraphStatsResponse)
async def get_stats(workspace: Optional[str] = None):
    """Get node, edge, and density statistics for project knowledge graph."""
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


@router.post("/build")
async def build_graph(workspace: Optional[str] = None):
    """Rebuild AST structural graph for current workspace."""
    ws = Path(workspace).resolve() if workspace else Path.cwd()
    engine = ProjectGraphEngine(ws)
    stats = engine.build_graph()
    return {
        "status": "success",
        "nodes_indexed": stats.total_nodes,
        "edges_indexed": stats.total_edges,
    }
