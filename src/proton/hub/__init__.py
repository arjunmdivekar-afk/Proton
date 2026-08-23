"""Proton Model Hub package for Transformers and Hugging Face integration."""

from proton.hub.client import HuggingFaceHubClient, HubModelSummary, HubModelDetails
from proton.hub.downloader import ModelDownloader, DownloadProgress
from proton.hub.hardware import detect_hardware, assess_model_fit, HardwareProfile, HardwareFitVerdict
from proton.hub.registry import ModelRegistry, InstalledModelRecord

__all__ = [
    "HuggingFaceHubClient",
    "HubModelSummary",
    "HubModelDetails",
    "ModelDownloader",
    "DownloadProgress",
    "detect_hardware",
    "assess_model_fit",
    "HardwareProfile",
    "HardwareFitVerdict",
    "ModelRegistry",
    "InstalledModelRecord",
]
