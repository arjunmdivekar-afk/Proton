"""Health and server info routes with Python client examples."""

import time
from pathlib import Path
from fastapi import APIRouter, Request

from proton.server.schemas import HealthResponse, ServerInfoResponse
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager

router = APIRouter(prefix="/v1", tags=["Health & System"])
start_time = time.time()


@router.get(
    "/health",
    summary="Server Health & Active Model Status",
    response_model=HealthResponse,
)
async def get_health(request: Request) -> HealthResponse:
    """
    Get server status, software version, uptime, system load, active AI provider, and active model.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/health"
    response = requests.get(url)
    health = response.json()
    print(f"Status: {health['status']} (v{health['version']})")
    print(f"Active Model: {health['active_model']}")
    print(f"Provider: {health['provider_type']} ({health['base_url']})")
    ```
    """
    config_mgr = ConfigManager()
    conn_mgr = ConnectionManager()
    active_conn = conn_mgr.get_active_connection()

    return HealthResponse(
        status="ok",
        version="2.6.4",
        uptime_seconds=round(time.time() - start_time, 2),
        workspace=str(Path.cwd().resolve()),
        active_connection=active_conn.id if active_conn else None,
        active_model=config_mgr.config.active_model,
        provider_type=active_conn.provider.value if active_conn else None,
        base_url=active_conn.base_url if active_conn else None,
    )


@router.get(
    "/info",
    summary="Server Endpoints & Capability Manifest",
    response_model=ServerInfoResponse,
)
async def get_info(request: Request) -> ServerInfoResponse:
    """
    List available API capabilities, documentation URLs, and OpenAPI specification.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/info"
    response = requests.get(url)
    info = response.json()
    print("Documentation:", info["docs_url"])
    print("Total Endpoints:", len(info["endpoints"]))
    ```
    """
    return ServerInfoResponse(
        name="Proton Autonomous AI Server",
        version="2.6.4",
        docs_url="/docs",
        openapi_url="/openapi.json",
        endpoints=[
            "POST /v1/chat",
            "POST /v1/agents/run",
            "POST /v1/tasks",
            "GET  /v1/tasks",
            "GET  /v1/tasks/{id}",
            "POST /v1/tasks/{id}/run",
            "GET  /v1/memory",
            "POST /v1/memory",
            "POST /v1/memory/search",
            "GET  /v1/graph/impact",
            "GET  /v1/graph/stats",
            "POST /v1/graph/build",
            "POST /v1/rag/search",
            "POST /v1/rag/index",
            "GET  /v1/inspect",
            "POST /v1/benchmark/run",
            "GET  /v1/security",
            "POST /v1/security/test",
            "GET  /v1/security/audit",
            "GET  /v1/tools",
            "POST /v1/tools/execute",
            "GET  /v1/models",
            "GET  /v1/providers",
            "GET  /v1/connections",
            "POST /v1/connections/switch",
            "GET  /v1/health",
        ],
    )
