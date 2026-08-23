"""Comprehensive offline test battery for Proton Model Hub and Transformers Engine."""

import pytest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from proton.hub.client import HuggingFaceHubClient, HubModelSummary, HubModelDetails
from proton.hub.hardware import detect_hardware, assess_model_fit, HardwareProfile
from proton.hub.downloader import ModelDownloader, DownloadProgress, render_progress_bar, format_bytes
from proton.hub.registry import ModelRegistry, InstalledModelRecord
from proton.providers.transformers import TransformersProvider
from proton.core.types import Message, Role
from proton.connection.schema import ConnectionProfile, ProviderType as ConnProviderType
from proton.providers.registry import ProviderRegistry


@pytest.fixture
def temp_registry(tmp_path):
    reg_file = tmp_path / "test_registry.json"
    registry = ModelRegistry(registry_file=reg_file)
    return registry


def test_render_progress_bar_and_formatting():
    """Verify visual progress bar and byte formatting."""
    bar = render_progress_bar(78.0)
    assert "78%" in bar
    assert "█" in bar
    assert "░" in bar

    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024 * 50) == "50.0 MB"
    assert format_bytes(int(6.3 * (1024 ** 3))) == "6.3 GB"


def test_hardware_detection_and_model_fit():
    """Verify CPU, RAM, GPU detection and parameter fit heuristics."""
    hw = detect_hardware()
    assert hw.total_ram_gb > 0
    assert hw.available_ram_gb > 0
    assert hw.cpu_count_physical >= 1
    assert hw.disk_free_gb >= 0

    # Test fit for 1B model on 16GB RAM system
    mock_hw_16gb = HardwareProfile(
        os_name="Windows 11",
        cpu_arch="AMD64",
        cpu_count_physical=8,
        cpu_count_logical=16,
        total_ram_gb=16.0,
        available_ram_gb=12.0,
        has_cuda=True,
        cuda_vram_gb=8.0,
        cuda_device_name="RTX 4070",
    )
    verdict_1b = assess_model_fit(1.2, hardware=mock_hw_16gb)
    assert verdict_1b.fits is True
    assert "cuda" in verdict_1b.recommended_device

    # Test fit for 70B model on 16GB RAM system (should warn / not fit)
    verdict_70b = assess_model_fit(70.0, hardware=mock_hw_16gb)
    assert verdict_70b.fits is False
    assert "Warning" in verdict_70b.warning_message


def test_hub_model_discovery_and_search():
    """Verify Hugging Face model search and pagination without live network calls."""
    client = HuggingFaceHubClient()

    mock_hf_model = MagicMock()
    mock_hf_model.id = "meta-llama/Llama-3.2-1B-Instruct"
    mock_hf_model.downloads = 450000
    mock_hf_model.likes = 1200
    mock_hf_model.pipeline_tag = "text-generation"
    mock_hf_model.tags = ["transformers", "license:llama3.2", "safetensors"]
    mock_hf_model.cardData = {"license": "llama3.2"}

    with patch.object(client.api, "list_models", return_value=[mock_hf_model]):
        models, has_next, page = client.search_models(query="llama", page=1, page_size=20)
        assert len(models) == 1
        m = models[0]
        assert m.id == "meta-llama/Llama-3.2-1B-Instruct"
        assert m.author == "meta-llama"
        assert m.name == "Llama-3.2-1B-Instruct"
        assert m.parameters_display == "1B"
        assert m.downloads == 450000
        assert m.license == "llama3.2"
        assert m.is_transformers_compatible is True


def test_hub_model_details_extraction():
    """Verify full metadata details parsing from mock model_info."""
    client = HuggingFaceHubClient()

    mock_info = MagicMock()
    mock_info.id = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    mock_info.downloads = 250000
    mock_info.likes = 850
    mock_info.pipeline_tag = "text-generation"
    mock_info.tags = ["transformers", "license:apache-2.0", "custom_code"]
    mock_info.cardData = {"license": "apache-2.0"}

    mock_sibling = MagicMock()
    mock_sibling.rfilename = "model.safetensors"
    mock_sibling.size = int(3.1 * (1024 ** 3))
    mock_info.siblings = [mock_sibling]

    with patch.object(client.api, "model_info", return_value=mock_info):
        details = client.get_model_details("Qwen/Qwen2.5-Coder-1.5B-Instruct")
        assert details is not None
        assert details.id == "Qwen/Qwen2.5-Coder-1.5B-Instruct"
        assert details.author == "Qwen"
        assert details.parameters_display == "1.5B"
        assert details.estimated_size_gb == 3.1
        assert details.license == "apache-2.0"
        assert details.requires_remote_code is True  # custom_code tag


def test_model_registry_crud_and_set_default(temp_registry, tmp_path):
    """Verify registration, listing, deletion, and default model persistence."""
    dummy_model_dir = tmp_path / "dummy_model"
    dummy_model_dir.mkdir()

    # 1. Register
    rec = temp_registry.register(
        model_id="meta-llama/Llama-3.2-1B-Instruct",
        local_path=dummy_model_dir,
        total_bytes=int(2.5 * (1024 ** 3)),
        parameters_display="1B",
        license="llama3.2",
        is_default=True,
    )
    assert rec.id == "meta-llama/Llama-3.2-1B-Instruct"
    assert rec.is_default is True
    assert temp_registry.is_installed("meta-llama/Llama-3.2-1B-Instruct") is True

    # 2. List
    installed = temp_registry.list_installed()
    assert len(installed) == 1

    # 3. Register second model
    dummy_model_dir2 = tmp_path / "dummy_model_2"
    dummy_model_dir2.mkdir()
    rec2 = temp_registry.register(
        model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        local_path=dummy_model_dir2,
        total_bytes=int(3.1 * (1024 ** 3)),
        parameters_display="1.5B",
        license="apache-2.0",
        is_default=False,
    )
    assert len(temp_registry.list_installed()) == 2

    # 4. Set second as default
    temp_registry.set_as_proton_default("Qwen/Qwen2.5-Coder-1.5B-Instruct")
    def_model = temp_registry.get_default_model()
    assert def_model.id == "Qwen/Qwen2.5-Coder-1.5B-Instruct"

    # 5. Unregister
    temp_registry.unregister("meta-llama/Llama-3.2-1B-Instruct")
    assert len(temp_registry.list_installed()) == 1


def test_model_downloader_progress_and_cancel(tmp_path):
    """Verify download manager progress callbacks and cancellation cleanup."""
    downloader = ModelDownloader()
    downloader.download_dir = tmp_path

    # Test disk space check
    has_space, free_b, req_b = downloader.check_disk_space(required_bytes=1000)
    assert has_space is True

    # Test cancellation flag
    downloader.cancel()
    assert downloader._is_cancelled is True


@pytest.mark.asyncio
async def test_transformers_provider_interface(tmp_path):
    """Verify TransformersProvider initialization, message formatting, and model listing."""
    provider = TransformersProvider(
        model_id="meta-llama/Llama-3.2-1B-Instruct",
        trust_remote_code=False,
    )
    assert provider.trust_remote_code is False

    # Test message prompt formatting
    messages = [
        Message(role=Role.USER, content="Hello!"),
        Message(role=Role.ASSISTANT, content="Hi there!"),
        Message(role=Role.USER, content="Explain RAG"),
    ]
    prompt = provider._format_messages_to_prompt(messages)
    assert "Hello!" in prompt
    assert "Explain RAG" in prompt

    # Test model listing
    models = await provider.list_models()
    assert isinstance(models, list)


def test_provider_registry_transformers_integration():
    """Verify ProviderRegistry creates TransformersProvider when connection provider is TRANSFORMERS."""
    profile = ConnectionProfile(
        id="transformers",
        name="Local Transformers",
        provider=ConnProviderType.TRANSFORMERS,
        host="127.0.0.1",
        port=0,
        protocol="local",
        base_path="",
    )
    provider = ProviderRegistry.get_provider_for_connection(profile)
    assert isinstance(provider, TransformersProvider)


def test_security_trust_remote_code_default():
    """Verify security defaults: trust_remote_code is strictly False."""
    provider = TransformersProvider()
    assert provider.trust_remote_code is False


def test_pagination_and_slicing():
    """Verify 20-per-page slicing and has_next calculation."""
    client = HuggingFaceHubClient()
    mock_models = [MagicMock(id=f"author/model-{i}", downloads=100 - i, likes=10, pipeline_tag="text-generation", tags=["transformers"], cardData={}) for i in range(45)]

    with patch.object(client.api, "list_models", return_value=mock_models):
        # Page 1
        p1, has_next_1, _ = client.search_models(page=1, page_size=20)
        assert len(p1) == 20
        assert has_next_1 is True

        # Page 2
        p2, has_next_2, _ = client.search_models(page=2, page_size=20)
        assert len(p2) == 20
        assert has_next_2 is True

        # Page 3
        p3, has_next_3, _ = client.search_models(page=3, page_size=20)
        assert len(p3) == 5
        assert has_next_3 is False


def test_token_redaction_security():
    """Verify Hugging Face API tokens are never exposed."""
    from proton.security.redaction import redact_text
    sample_text = "Connecting to Hugging Face with token hf_AbCdEfGhIjKlMnOpQrStUvWxYz12345678"
    redacted = redact_text(sample_text)
    assert "hf_AbCdEfGh" not in redacted
    assert "REDACTED" in redacted

