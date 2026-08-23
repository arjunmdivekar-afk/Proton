"""Model Benchmark API routes with Python client examples."""

import json
from fastapi import APIRouter

from proton.benchmark.runner import BenchmarkRunner
from proton.core.config import get_proton_home

router = APIRouter(prefix="/v1/benchmark", tags=["Model Benchmarks"])


@router.post(
    "/run",
    summary="Run LLM Capability Benchmark",
)
async def run_benchmark(quick: bool = False):
    """
    Run 8-dimension model benchmark testing Latency, Tok/s, Context, Tools, RAG, Coding, Planning, and Error Recovery.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/benchmark/run"
    response = requests.post(url, params={"quick": False}, timeout=180.0)
    data = response.json()
    print(f"Overall Rating: [{data['overall_grade']}] {data['overall_score']} / 100")
    print(f"Speed: {data['tokens_per_second']:.1f} tokens/sec")
    print(f"Agent Readiness: {data['agent_readiness']}")
    ```
    """
    runner = BenchmarkRunner(quick=quick)
    report = await runner.run_benchmark()
    return report.model_dump(mode="json")


@router.get(
    "/history",
    summary="Get Historical Benchmark Runs",
)
async def get_benchmark_history():
    """
    Retrieve historical model benchmark evaluations and scores.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/benchmark/history"
    response = requests.get(url)
    history = response.json()
    print(f"Total Past Runs: {history['total']}")
    ```
    """
    history_path = get_proton_home() / "benchmarks.json"
    if not history_path.exists():
        return {"total": 0, "history": []}

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
        return {"total": len(data), "history": data}
    except Exception:
        return {"total": 0, "history": []}
