"""Developer dashboard and live log streaming router for Proton Web UI."""

import asyncio
import json
import socket
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from proton.connection.manager import ConnectionManager
from proton.core.config import ConfigManager
from proton.hub.hardware import detect_hardware
from proton.hub.registry import ModelRegistry

router = APIRouter(prefix="/v1/developer", tags=["Developer"])

_DEV_LOGS: List[Dict[str, Any]] = [
    {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "tag": "SERVER",
        "message": "Proton Autonomous AI Server initialized on local port.",
    },
    {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "tag": "SYSTEM",
        "message": "Hardware acceleration profile loaded. In-process inference engine ready.",
    },
]


def get_lan_ip() -> str:
    """Detect LAN IP address on the local WiFi network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def append_dev_log(level: str, tag: str, message: str) -> None:
    """Record a developer log entry."""
    _DEV_LOGS.append({
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "tag": tag,
        "message": message,
    })
    if len(_DEV_LOGS) > 1000:
        _DEV_LOGS.pop(0)


@router.get("/status")
async def get_developer_status() -> Dict[str, Any]:
    """Get developer dashboard metrics, loaded models, reachability, and hardware status."""
    config_mgr = ConfigManager()
    conn_mgr = ConnectionManager(config_mgr)
    reg = ModelRegistry()

    lan_ip = get_lan_ip()
    port = 8787
    active_conn = conn_mgr.get_active_connection()
    installed_models = reg.list_installed()
    active_model = config_mgr.config.active_model or (installed_models[0].id if installed_models else "None")
    hw = detect_hardware()

    return {
        "status": "running",
        "version": "2.6.4",
        "uptime_seconds": round(time.time()),
        "local_url": f"http://127.0.0.1:{port}",
        "lan_url": f"http://{lan_ip}:{port}",
        "reachability": f"http://{lan_ip}:{port}",
        "docs_url": f"http://{lan_ip}:{port}/docs",
        "active_provider": active_conn.provider.value,
        "active_connection": active_conn.name,
        "active_model": active_model,
        "loaded_models": [
            {
                "id": m.id,
                "name": m.name,
                "size_gb": m.size_gb,
                "parameters": m.parameters_display,
                "is_default": m.id == active_model,
            }
            for m in installed_models
        ],
        "hardware": {
            "device_mode": config_mgr.config.device_mode or "auto",
            "has_cuda": hw.has_cuda,
            "gpu_name": hw.cuda_device_name or "None (CPU Mode)",
            "total_ram_gb": round(hw.total_ram_gb, 1),
            "free_ram_gb": round(hw.available_ram_gb, 1),
            "total_vram_gb": round(hw.cuda_vram_gb, 1) if hw.cuda_vram_gb else 0,
        },
        "plugins": [
            {"name": "duckduckgo_search", "type": "web_tool", "status": "active"},
            {"name": "ast_code_analyzer", "type": "rag_graph", "status": "active"},
            {"name": "filesystem_sandbox", "type": "security", "status": "active"},
            {"name": "shell_executor", "type": "terminal", "status": "active"},
        ],
    }


@router.get("/logs")
async def get_developer_logs() -> Dict[str, Any]:
    """Get all recent developer logs."""
    return {"logs": _DEV_LOGS}


@router.post("/logs/clear")
async def clear_developer_logs() -> Dict[str, Any]:
    """Clear developer log history."""
    _DEV_LOGS.clear()
    append_dev_log("INFO", "SERVER", "Developer log stream cleared.")
    return {"success": True}


@router.get("/logs/stream")
async def stream_developer_logs() -> StreamingResponse:
    """Stream live developer events over Server-Sent Events (SSE)."""
    async def event_generator() -> AsyncGenerator[str, None]:
        last_idx = 0
        while True:
            if last_idx < len(_DEV_LOGS):
                for entry in _DEV_LOGS[last_idx:]:
                    yield f"data: {json.dumps(entry)}\n\n"
                last_idx = len(_DEV_LOGS)
            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
