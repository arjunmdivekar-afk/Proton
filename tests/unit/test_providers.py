"""Unit tests for model provider abstraction and OpenAI-compatible adapter."""

import pytest
from proton.providers.openai_compatible import OpenAICompatibleProvider
from proton.providers.lmstudio import LMStudioProvider
from proton.providers.ollama import OllamaProvider
from proton.core.types import Message, Role


def test_provider_initialization():
    lm = LMStudioProvider(base_url="http://192.168.1.50:1234/v1")
    assert lm.base_url == "http://192.168.1.50:1234/v1"

    ol = OllamaProvider(base_url="http://127.0.0.1:11434/v1")
    assert ol.base_url == "http://127.0.0.1:11434/v1"


def test_provider_message_formatting():
    p = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
    messages = [
        Message(role=Role.SYSTEM, content="System instructions"),
        Message(role=Role.SYSTEM, content="RAG Context data"),
        Message(role=Role.USER, content="Hello"),
    ]
    formatted = p._format_messages(messages)
    assert len(formatted) == 2
    assert formatted[0]["role"] == "system"
    assert "System instructions" in formatted[0]["content"]
    assert "RAG Context data" in formatted[0]["content"]
    assert formatted[1]["role"] == "user"


def test_provider_tool_message_formatting():
    p = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
    messages = [
        Message(
            role=Role.ASSISTANT,
            content="",
            tool_calls=[{"id": "call_123", "name": "read_file", "arguments": {"path": "a.py"}}],
        ),
        Message(
            role=Role.TOOL,
            content="print('hello')",
            tool_call_id="call_123",
        ),
    ]
    formatted = p._format_messages(messages)
    assert len(formatted) == 2
    # Check assistant tool_calls format
    asst_msg = formatted[0]
    assert asst_msg["role"] == "assistant"
    assert "tool_calls" in asst_msg
    assert asst_msg["tool_calls"][0]["id"] == "call_123"
    assert asst_msg["tool_calls"][0]["type"] == "function"
    assert asst_msg["tool_calls"][0]["function"]["name"] == "read_file"
    assert asst_msg["tool_calls"][0]["function"]["arguments"] == '{"path": "a.py"}'

    # Check tool response format
    tool_msg = formatted[1]
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "call_123"
    assert tool_msg["content"] == "print('hello')"


@pytest.mark.asyncio
async def test_fallback_embeddings():
    p = OpenAICompatibleProvider(base_url="http://non-existent-host:9999/v1")
    # Should fallback gracefully to deterministic token hash vectors
    vecs = await p.embed(["quicksort algorithm in python", "quicksort algorithm in python"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 128
    # Identical texts must produce identical vectors
    assert vecs[0] == vecs[1]
