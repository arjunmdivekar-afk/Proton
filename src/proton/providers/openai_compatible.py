"""OpenAI-compatible inference server provider (LM Studio, vLLM, llama.cpp, LocalAI)."""

import json
from typing import AsyncGenerator, Dict, List, Optional, Any
import httpx

from proton.providers.base import ModelProvider, StreamChunk, ChatResponse
from proton.core.types import Message, ToolCall, ModelInfo, ModelCapabilities, Role
from proton.core.exceptions import ProviderError, ConnectionError


class OpenAICompatibleProvider(ModelProvider):
    """Provider for OpenAI-compatible REST API endpoints."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        if custom_headers:
            self.headers.update(custom_headers)

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        system_parts = []
        conversation_messages = []

        for m in messages:
            if m.role == Role.SYSTEM:
                if m.content and m.content.strip():
                    system_parts.append(m.content.strip())
            else:
                conversation_messages.append(m)

        formatted = []
        if system_parts:
            # Single consolidated system message at index 0 for strict Jinja compliance
            formatted.append({"role": "system", "content": "\n\n".join(system_parts)})

        for m in conversation_messages:
            msg_dict: Dict[str, Any] = {"role": m.role.value, "content": m.content or ""}
            if m.name and m.role != Role.TOOL:
                msg_dict["name"] = m.name

            if m.role == Role.ASSISTANT and m.tool_calls:
                formatted_tool_calls = []
                for tc in m.tool_calls:
                    if "function" in tc and isinstance(tc["function"], dict):
                        formatted_tool_calls.append(tc)
                    else:
                        args = tc.get("arguments", {})
                        args_str = json.dumps(args) if isinstance(args, (dict, list)) else str(args)
                        formatted_tool_calls.append({
                            "id": tc.get("id", "call_0"),
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": args_str,
                            },
                        })
                msg_dict["tool_calls"] = formatted_tool_calls

            elif m.role == Role.TOOL:
                msg_dict["tool_call_id"] = m.tool_call_id or "call_0"

            formatted.append(msg_dict)
        return formatted

    async def stream_chat(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {**self.headers, "Accept": "text/event-stream"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        err_text = await resp.aread()
                        raise ProviderError(f"Provider returned HTTP {resp.status_code}: {err_text.decode('utf-8', 'ignore')}")

                    tool_call_collector: Dict[int, Dict[str, Any]] = {}

                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or line in ("data: [DONE]", "[DONE]", "event: done"):
                            continue

                        json_str = line
                        if json_str.startswith("data:"):
                            json_str = json_str[5:].strip()

                        if not json_str or json_str == "[DONE]":
                            continue

                        try:
                            data = json.loads(json_str)
                        except json.JSONDecodeError:
                            continue

                        if "error" in data:
                            err_msg = data["error"]
                            if isinstance(err_msg, dict):
                                err_msg = err_msg.get("message", str(err_msg))
                            raise ProviderError(f"Provider Error: {err_msg}")

                        usage_info = data.get("usage")
                        choices = data.get("choices", [])
                        text = ""
                        finish_reason = None

                        if choices:
                            choice = choices[0]
                            delta = choice.get("delta", {})
                            msg = choice.get("message", {})
                            finish_reason = choice.get("finish_reason")

                            # Text delta (supports content, reasoning_content, thought, text, message content)
                            text = (
                                delta.get("content")
                                or delta.get("reasoning_content")
                                or delta.get("thought")
                                or delta.get("text")
                                or msg.get("content")
                                or msg.get("reasoning_content")
                                or choice.get("text")
                                or ""
                            )

                            # Tool call streaming chunks
                            delta_tools = delta.get("tool_calls") or msg.get("tool_calls")
                            if delta_tools:
                                for tc in delta_tools:
                                    idx = tc.get("index", 0)
                                    if idx not in tool_call_collector:
                                        tool_call_collector[idx] = {
                                            "id": tc.get("id", f"call_{idx}"),
                                            "name": tc.get("function", {}).get("name", ""),
                                            "arguments": "",
                                        }
                                    if "function" in tc and "name" in tc["function"] and tc["function"]["name"]:
                                        tool_call_collector[idx]["name"] = tc["function"]["name"]
                                    if "function" in tc and "arguments" in tc["function"]:
                                        tool_call_collector[idx]["arguments"] += tc["function"]["arguments"]

                        elif "message" in data:
                            msg = data.get("message", {})
                            text = msg.get("content") or msg.get("reasoning_content") or ""
                            finish_reason = "stop" if data.get("done") else None
                        elif "response" in data:
                            text = data.get("response") or ""
                            finish_reason = "stop" if data.get("done") else None

                        parsed_tools: Optional[List[ToolCall]] = None
                        valid_collected = [
                            tc_data for tc_data in tool_call_collector.values()
                            if tc_data.get("name", "").strip()
                        ]
                        if finish_reason == "tool_calls" or (finish_reason and valid_collected):
                            parsed_tools = []
                            for tc_data in valid_collected:
                                try:
                                    args = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
                                except json.JSONDecodeError:
                                    args = {"raw": tc_data["arguments"]}
                                parsed_tools.append(
                                    ToolCall(
                                        id=tc_data["id"],
                                        name=tc_data["name"].strip(),
                                        arguments=args,
                                    )
                                )
                        elif finish_reason and not valid_collected and tool_call_collector:
                            # If model emitted arguments without a tool name, yield arguments as regular text
                            for tc_data in tool_call_collector.values():
                                raw_args = tc_data.get("arguments", "")
                                if raw_args and not text:
                                    text = raw_args

                        if text or parsed_tools or finish_reason or usage_info:
                            yield StreamChunk(
                                delta=text,
                                tool_calls=parsed_tools if parsed_tools else None,
                                finish_reason=finish_reason,
                                usage=usage_info,
                            )

        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to AI server at {url}: {e}")
        except httpx.TimeoutException:
            raise ProviderError(f"Request to AI server at {url} timed out.")

    async def chat_complete(
        self,
        messages: List[Message],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code != 200:
                    raise ProviderError(f"Provider returned HTTP {resp.status_code}: {resp.text}")
                data = resp.json()
                choice = data["choices"][0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""
                tool_calls = None
                if "tool_calls" in msg and msg["tool_calls"]:
                    tool_calls = []
                    for tc in msg["tool_calls"]:
                        fn = tc.get("function", {})
                        try:
                            args = json.loads(fn.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            args = {"raw": fn.get("arguments", "")}
                        tool_calls.append(ToolCall(id=tc.get("id", ""), name=fn.get("name", ""), arguments=args))

                return ChatResponse(
                    content=content,
                    tool_calls=tool_calls,
                    finish_reason=choice.get("finish_reason"),
                    usage=data.get("usage", {}),
                    model=data.get("model", model),
                )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to AI server at {url}: {e}")
        except httpx.TimeoutException:
            raise ProviderError(f"Request to AI server at {url} timed out.")

    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        # Only call remote embeddings endpoint if an embedding model is explicitly specified.
        # Otherwise, use fast in-process embeddings to prevent LM Studio from swapping out
        # the main chat model from GPU VRAM on every turn.
        if not model:
            return self._fallback_embed(texts)

        url = f"{self.base_url}/embeddings"
        payload = {"input": texts, "model": model}
        try:
            async with httpx.AsyncClient(timeout=min(3.0, self.timeout)) as client:
                resp = await client.post(url, headers=self.headers, json=payload)
                if resp.status_code != 200:
                    return self._fallback_embed(texts)
                data = resp.json()
                embeddings = [item["embedding"] for item in data.get("data", [])]
                return embeddings
        except Exception:
            return self._fallback_embed(texts)

    def _fallback_embed(self, texts: List[str], dim: int = 128) -> List[List[float]]:
        """Fast in-process token-hash fallback embeddings when server has no embedding model loaded."""
        results = []
        for text in texts:
            vec = [0.0] * dim
            words = text.lower().split()
            if not words:
                results.append(vec)
                continue
            for w in words:
                h = hash(w) % dim
                vec[h] += 1.0
            norm = sum(x * x for x in vec) ** 0.5
            if norm > 0:
                vec = [x / norm for x in vec]
            results.append(vec)
        return results

    async def list_models(self) -> List[ModelInfo]:
        url = f"{self.base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                models = []
                for item in data.get("data", []):
                    mid = item.get("id")
                    if mid:
                        models.append(ModelInfo(id=mid, name=mid, provider="openai_compatible", capabilities=ModelCapabilities()))
                return models
        except Exception:
            return []
