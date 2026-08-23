"""Chat completion and token streaming routes."""

import json
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from proton.server.schemas import ChatRequest, ChatResponse
from proton.core.types import Message, Role
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry
from proton.agent.context import ContextAssembler

router = APIRouter(prefix="/v1", tags=["Chat & Streaming"])


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """Generate a chat response. Supports standard JSON and Server-Sent Events (SSE) streaming."""
    config_mgr = ConfigManager()
    conn_mgr = ConnectionManager()
    active_conn = conn_mgr.get_active_connection()

    if not active_conn:
        raise HTTPException(status_code=503, detail="No active AI connection configured in Proton.")

    provider = ProviderRegistry.get_provider_for_connection(active_conn)
    model_id = request.model or config_mgr.config.active_model or "default"

    # Convert request messages to Proton Messages
    proton_messages = [
        Message(
            role=Role(m.role.lower()) if m.role.lower() in ("system", "user", "assistant") else Role.USER,
            content=m.content,
        )
        for m in request.messages
    ]

    # Context enrichment with categorized memory / RAG if requested
    if request.use_memory:
        assembler = ContextAssembler(workspace_root=Path.cwd())
        sys_msg = assembler.build_system_message()
        if not any(m.role == Role.SYSTEM for m in proton_messages):
            proton_messages.insert(0, sys_msg)

    start_time = time.perf_counter()

    if request.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            chat_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            try:
                async for chunk in provider.stream_chat(
                    messages=proton_messages,
                    model=model_id,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                ):
                    text = chunk.text if hasattr(chunk, "text") else str(chunk)
                    if text:
                        data = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": model_id,
                            "choices": [{"delta": {"content": text}, "index": 0, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(data)}\n\n"

                # Send final done chunk
                done_data = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "model": model_id,
                    "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(done_data)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                err_data = {"error": {"message": str(e), "type": "provider_error"}}
                yield f"data: {json.dumps(err_data)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Non-streaming execution
    try:
        full_content = ""
        async for chunk in provider.stream_chat(
            messages=proton_messages,
            model=model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ):
            text = chunk.text if hasattr(chunk, "text") else str(chunk)
            full_content += text

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            model=model_id,
            content=full_content,
            role="assistant",
            usage={"total_tokens": len(full_content.split())},
            duration_ms=duration_ms,
        )
    except Exception as e:
        err_msg = str(e)
        if "connect" in err_msg.lower() or "connection" in err_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Cannot reach AI inference runtime at {active_conn.base_url}. Ensure LM Studio or Ollama is running.",
            )
        raise HTTPException(status_code=500, detail=f"Inference error: {err_msg}")
