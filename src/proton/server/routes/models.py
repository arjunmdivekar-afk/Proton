"""Models, Providers, and Connections API routes with Python client examples."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException

from proton.server.schemas import ConnectionSwitchRequest, ModelSwitchRequest
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry

router = APIRouter(prefix="/v1", tags=["Models & Providers"])


@router.get(
    "/models",
    summary="List Discovered AI Models",
)
async def list_models():
    """
    List all available models discovered dynamically from the active AI provider runtime.

    ---

    ### 🐍 Python Example:
    ```python
    import requests

    url = "http://127.0.0.1:8787/v1/models"
    response = requests.get(url)
    data = response.json()
    print(f"Active Model: {data['active_model']}")
    print(f"Provider: {data['provider']} ({data['base_url']})")
    for m in data["models"]:
        print(f"- {m['id']} (Context: {m.get('context_window')})")
    ```
    """
    conn_mgr = ConnectionManager()
    active_conn = conn_mgr.get_active_connection()
    if not active_conn:
        return {"active_model": None, "models": []}

    provider = ProviderRegistry.get_provider_for_connection(active_conn)
    config_mgr = ConfigManager()

    try:
        models = await provider.list_models()
        return {
            "active_model": config_mgr.config.active_model,
            "provider": active_conn.provider.value,
            "base_url": active_conn.base_url,
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "context_window": m.context_window,
                    "supports_tools": m.capabilities.supports_tools,
                    "supports_streaming": m.capabilities.supports_streaming,
                }
                for m in models
            ],
        }
    except Exception as e:
        return {
            "active_model": config_mgr.config.active_model,
            "provider": active_conn.provider.value,
            "base_url": active_conn.base_url,
            "models": [{"id": config_mgr.config.active_model or "default", "name": config_mgr.config.active_model or "default"}],
            "error": str(e),
        }


@router.get(
    "/models/hub/search",
    summary="Search Proton Model Hub",
)
async def search_hub_models(q: str = "", page: int = 1):
    """Search Proton Model Hub and Hugging Face catalog."""
    from proton.hub.client import HuggingFaceHubClient
    from proton.hub.registry import ModelRegistry

    reg = ModelRegistry()
    installed = {m.id: m for m in reg.list_installed()}

    client = HuggingFaceHubClient()
    try:
        results, has_next, total = client.search_models(query=q if q.strip() else None, page=page, page_size=20)
        models = [
            {
                "id": m.id,
                "name": m.name,
                "size_gb": m.estimated_size_gb,
                "size_display": f"{m.estimated_size_gb:.1f} GB" if m.estimated_size_gb else "Auto",
                "parameters": m.parameters_display,
                "downloads_display": f"{m.downloads:,}" if m.downloads else "10k+",
                "description": f"{m.architecture} | {m.license}",
                "license": m.license,
                "is_installed": m.id in installed,
            }
            for m in results
        ]
        return {"models": models, "total": total, "has_next": has_next, "page": page}
    except Exception as e:
        return {"models": [], "total": 0, "has_next": False, "page": page, "error": str(e)}


@router.get(
    "/connections",
    summary="List Configured AI Endpoints",
)
@router.get(
    "/connection/list",
    include_in_schema=False,
)
async def list_connections():
    """List all configured AI endpoints with real-time latency and connection status."""
    from proton.connection.probe import probe_connection

    conn_mgr = ConnectionManager()
    conns = conn_mgr.list_connections()
    active_conn = conn_mgr.get_active_connection()

    connection_data = []
    for c in conns:
        latency = None
        status = "offline"

        if c.provider.value in ("proton-hub", "transformers") or c.protocol == "local":
            latency = 0.1
            status = "connected"
        else:
            try:
                probe_res = await probe_connection(c)
                if probe_res.success:
                    status = "connected"
                    latency = round(probe_res.latency_ms, 1) if probe_res.latency_ms else None
            except Exception:
                status = "offline"

        connection_data.append({
            "id": c.id,
            "name": c.name,
            "provider": c.provider.value,
            "base_url": c.base_url,
            "is_active": (c.id == active_conn.id) if active_conn else False,
            "status": status,
            "latency_ms": latency,
            "models_count": len(c.discovered_models) if c.discovered_models else 0,
        })

    return {
        "active_connection": active_conn.id if active_conn else None,
        "connections": connection_data,
    }


@router.post(
    "/connections/test",
    summary="Test Connection Latency",
)
async def test_connection_endpoint(req: dict):
    """Test live connectivity and latency for an AI endpoint."""
    from proton.connection.probe import probe_connection
    from proton.connection.schema import ConnectionProfile, ProviderType

    conn_id = req.get("connection_id")
    conn_mgr = ConnectionManager()

    if conn_id:
        profile = conn_mgr.get_connection(conn_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Connection '{conn_id}' not found.")
    else:
        provider_str = req.get("provider", "openai")
        try:
            prov_type = ProviderType(provider_str)
        except Exception:
            prov_type = ProviderType.OPENAI_COMPATIBLE

        profile = ConnectionProfile(
            id=req.get("name", "custom").lower().replace(" ", "-"),
            name=req.get("name", "Custom Connection"),
            provider=prov_type,
            host=req.get("host", "127.0.0.1"),
            port=int(req.get("port", 1234)),
            protocol=req.get("protocol", "http"),
            base_path=req.get("base_path", "/v1"),
            api_key=req.get("api_key"),
        )

    res = await probe_connection(profile)
    return {
        "success": res.success,
        "latency_ms": round(res.latency_ms, 2) if res.latency_ms else None,
        "error": res.error_message,
        "discovered_models": res.discovered_models,
    }


@router.post(
    "/connections/switch",
    summary="Switch Active AI Endpoint",
)
@router.post(
    "/connection/active",
    include_in_schema=False,
)
async def switch_connection(req: ConnectionSwitchRequest):
    """Switch the active inference endpoint connection."""
    conn_mgr = ConnectionManager()
    config_mgr = ConfigManager()

    conn = conn_mgr.get_connection(req.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Connection '{req.connection_id}' not found.")

    config_mgr.set_active_connection(req.connection_id)
    return {"status": "switched", "active_connection": req.connection_id, "base_url": conn.base_url}


@router.post(
    "/models/switch",
    summary="Switch Active Model ID",
)
async def switch_model(req: ModelSwitchRequest):
    """Switch the active model name used for code intelligence and reasoning."""
    config_mgr = ConfigManager()
    config_mgr.set_active_model(req.model_id)
    return {"status": "switched", "active_model": req.model_id}
