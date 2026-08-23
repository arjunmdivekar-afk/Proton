"""Health and server info routes."""

import time
from pathlib import Path
from fastapi import APIRouter, Request

from proton.server.schemas import HealthResponse, ServerInfoResponse
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager

router = APIRouter(prefix="/v1", tags=["Health & System"])
start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    """Get server status, active model, provider details, and system uptime."""
    config_mgr = ConfigManager()
    conn_mgr = ConnectionManager()
    active_conn = conn_mgr.get_active_connection()

    return HealthResponse(
        status="ok",
        version="2.4.4",
        uptime_seconds=round(time.time() - start_time, 2),
        workspace=str(Path.cwd().resolve()),
        active_connection=active_conn.id if active_conn else None,
        active_model=config_mgr.config.active_model,
        provider_type=active_conn.provider.value if active_conn else None,
        base_url=active_conn.base_url if active_conn else None,
    )


@router.get("/info", response_model=ServerInfoResponse)
async def get_info(request: Request) -> ServerInfoResponse:
    """List available API capabilities and documentation links."""
    return ServerInfoResponse(
        name="Proton Autonomous AI Server",
        version="2.4.4",
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
