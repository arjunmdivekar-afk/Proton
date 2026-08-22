"""Abstract Model Provider interface for Proton."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Any
from pydantic import BaseModel

from proton.core.types import Message, ToolCall, ModelInfo


class StreamChunk(BaseModel):
    delta: str = ""
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    usage: Dict[str, Any] = {}
    model: str


class ModelProvider(ABC):
    """Abstract base class for all AI model providers."""

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream chat tokens and tool calls."""
        pass

    @abstractmethod
    async def chat_complete(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """Non-streaming chat completion."""
        pass

    @abstractmethod
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate vector embeddings for input texts."""
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """Query available models from provider."""
        pass
