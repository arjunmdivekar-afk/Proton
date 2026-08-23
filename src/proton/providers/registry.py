"""Provider factory and registry for instantiating model providers."""

from typing import Dict, Optional
from proton.connection.schema import ConnectionProfile, ProviderType
from proton.providers.base import ModelProvider
from proton.providers.lmstudio import LMStudioProvider
from proton.providers.ollama import OllamaProvider
from proton.providers.openai_compatible import OpenAICompatibleProvider
from proton.providers.transformers import TransformersProvider


class ProviderRegistry:
    """Registry and factory for model provider instances."""

    _instances: Dict[str, ModelProvider] = {}

    @classmethod
    def get_provider_for_connection(cls, profile: ConnectionProfile) -> ModelProvider:
        """Instantiate or retrieve cached provider for a given ConnectionProfile."""
        cache_key = f"{profile.id}:{profile.base_url}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        provider: ModelProvider
        if profile.provider in (ProviderType.PROTON_HUB, ProviderType.TRANSFORMERS):
            from proton.core.config import ConfigManager
            cfg = ConfigManager()
            provider = TransformersProvider(
                model_id=cfg.config.active_model,
            )
        elif profile.provider == ProviderType.LMSTUDIO:
            provider = LMStudioProvider(
                base_url=profile.base_url,
                api_key=profile.api_key,
                custom_headers=profile.custom_headers,
                timeout=profile.timeout_seconds,
            )
        elif profile.provider == ProviderType.OLLAMA:
            provider = OllamaProvider(
                base_url=profile.base_url,
                api_key=profile.api_key,
                custom_headers=profile.custom_headers,
                timeout=profile.timeout_seconds,
            )
        else:
            provider = OpenAICompatibleProvider(
                base_url=profile.base_url,
                api_key=profile.api_key,
                custom_headers=profile.custom_headers,
                timeout=profile.timeout_seconds,
            )

        cls._instances[cache_key] = provider
        return provider

    @classmethod
    def clear_cache(cls) -> None:
        cls._instances.clear()
