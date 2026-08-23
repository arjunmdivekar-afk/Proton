"""Models, Providers, and Connections API routes."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException

from proton.server.schemas import ConnectionSwitchRequest, ModelSwitchRequest
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry

router = APIRouter(prefix="/v1", tags=["Models & Providers"])


@router.get("/models")
async def list_models():
    """List all available models discovered from active AI provider."""
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


@router.get("/connections")
async def list_connections():
    """List all configured local and LAN AI endpoints (LM Studio, Ollama)."""
    conn_mgr = ConnectionManager()
    conns = conn_mgr.list_connections()
    active_conn = conn_mgr.get_active_connection()

    return {
        "active_connection": active_conn.id if active_conn else None,
        "connections": [
            {
                "id": c.id,
                "name": c.name,
                "provider": c.provider.value,
                "base_url": c.base_url,
                "is_active": (c.id == active_conn.id) if active_conn else False,
            }
            for c in conns
        ],
    }


@router.post("/connections/switch")
async def switch_connection(req: ConnectionSwitchRequest):
    """Switch active AI inference connection."""
    conn_mgr = ConnectionManager()
    config_mgr = ConfigManager()

    conn = conn_mgr.get_connection(req.connection_id)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Connection '{req.connection_id}' not found.")

    config_mgr.set_active_connection(req.connection_id)
    return {"status": "switched", "active_connection": req.connection_id, "base_url": conn.base_url}


@router.post("/models/switch")
async def switch_model(req: ModelSwitchRequest):
    """Switch active AI model."""
    config_mgr = ConfigManager()
    config_mgr.set_active_model(req.model_id)
    return {"status": "switched", "active_model": req.model_id}
