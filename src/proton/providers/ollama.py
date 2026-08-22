"""Ollama provider for Proton."""

from typing import Optional, Dict
from proton.providers.openai_compatible import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    """Ollama Model Provider (connecting via /v1 OpenAI compatibility layer)."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 180.0,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            custom_headers=custom_headers,
            timeout=timeout,
        )
