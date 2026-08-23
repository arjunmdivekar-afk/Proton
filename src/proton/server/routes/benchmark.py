"""Model Benchmark API routes."""

import json
from fastapi import APIRouter

from proton.benchmark.runner import BenchmarkRunner
from proton.core.config import get_proton_home

router = APIRouter(prefix="/v1/benchmark", tags=["Model Benchmarks"])


@router.post("/run")
async def run_benchmark(quick: bool = False):
    """Run multi-dimensional LLM benchmark (speed, tools, RAG, coding, planning, error recovery)."""
    runner = BenchmarkRunner(quick=quick)
    report = await runner.run_benchmark()
    return report.model_dump(mode="json")


@router.get("/history")
async def get_benchmark_history():
    """Retrieve history of past benchmark evaluations and model grades."""
    history_path = get_proton_home() / "benchmarks.json"
    if not history_path.exists():
        return {"total": 0, "history": []}

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
        return {"total": len(data), "history": data}
    except Exception:
        return {"total": 0, "history": []}
