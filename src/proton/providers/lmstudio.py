"""LM Studio provider for Proton (supports localhost and remote LAN IPs)."""

from typing import Optional, Dict
from proton.providers.openai_compatible import OpenAICompatibleProvider


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio Model Provider."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234/v1",
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
