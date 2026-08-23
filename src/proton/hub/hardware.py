"""System hardware detection and model capacity advisor for Proton."""

import os
import shutil
import platform
import psutil
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class HardwareProfile(BaseModel):
    """System hardware specification snapshot."""
    os_name: str
    cpu_arch: str
    cpu_count_physical: int
    cpu_count_logical: int
    total_ram_gb: float
    available_ram_gb: float
    has_cuda: bool = False
    cuda_device_count: int = 0
    cuda_device_name: Optional[str] = None
    cuda_vram_gb: float = 0.0
    has_mps: bool = False
    recommended_device: str = "cpu"
    disk_free_gb: float = 0.0


class HardwareFitVerdict(BaseModel):
    """Fit assessment for a specific model size."""
    fits: bool
    recommended_device: str
    estimated_ram_required_gb: float
    estimated_vram_required_gb: float
    warning_message: Optional[str] = None
    performance_tier: str = "Good"  # "Optimal", "Good", "Slow / Swapping", "Insufficient"


def detect_hardware() -> HardwareProfile:
    """Detect complete system hardware capabilities (CPU, RAM, GPU, VRAM, CUDA, MPS)."""
    mem = psutil.virtual_memory()
    total_ram_gb = round(mem.total / (1024 ** 3), 2)
    avail_ram_gb = round(mem.available / (1024 ** 3), 2)

    # Disk free in proton home / current drive
    total_d, used_d, free_d = shutil.disk_usage(os.getcwd())
    disk_free_gb = round(free_d / (1024 ** 3), 2)

    has_cuda = False
    cuda_count = 0
    cuda_name = None
    cuda_vram = 0.0
    has_mps = False

    try:
        import torch
        if torch.cuda.is_available():
            has_cuda = True
            cuda_count = torch.cuda.device_count()
            cuda_name = torch.cuda.get_device_name(0)
            cuda_vram = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            has_mps = True
    except Exception:
        pass

    rec_device = "cuda" if has_cuda else ("mps" if has_mps else "cpu")

    return HardwareProfile(
        os_name=f"{platform.system()} {platform.release()}",
        cpu_arch=platform.machine(),
        cpu_count_physical=psutil.cpu_count(logical=False) or 1,
        cpu_count_logical=psutil.cpu_count(logical=True) or 1,
        total_ram_gb=total_ram_gb,
        available_ram_gb=avail_ram_gb,
        has_cuda=has_cuda,
        cuda_device_count=cuda_count,
        cuda_device_name=cuda_name,
        cuda_vram_gb=cuda_vram,
        has_mps=has_mps,
        recommended_device=rec_device,
        disk_free_gb=disk_free_gb,
    )


def assess_model_fit(
    param_count_billions: float,
    precision_bytes: float = 2.0,  # 2 bytes for fp16/bf16, 0.5 for 4-bit, 1.0 for 8-bit
    hardware: Optional[HardwareProfile] = None,
) -> HardwareFitVerdict:
    """Assess if a model with given parameter count and precision fits on current hardware."""
    hw = hardware or detect_hardware()

    # Memory calculation: weights + 20% KV cache overhead
    weights_gb = (param_count_billions * 1e9 * precision_bytes) / (1024 ** 3)
    total_required_gb = round(weights_gb * 1.2, 2)

    if hw.has_cuda and hw.cuda_vram_gb > 0:
        if hw.cuda_vram_gb >= total_required_gb:
            return HardwareFitVerdict(
                fits=True,
                recommended_device="cuda",
                estimated_ram_required_gb=total_required_gb,
                estimated_vram_required_gb=total_required_gb,
                performance_tier="Optimal (Full GPU VRAM)",
            )
        elif hw.available_ram_gb + hw.cuda_vram_gb >= total_required_gb:
            return HardwareFitVerdict(
                fits=True,
                recommended_device="cuda:auto_split",
                estimated_ram_required_gb=total_required_gb,
                estimated_vram_required_gb=hw.cuda_vram_gb,
                warning_message=f"Model needs ~{total_required_gb}GB. GPU VRAM ({hw.cuda_vram_gb}GB) will offload remainder to RAM.",
                performance_tier="Good (GPU + RAM Offload)",
            )

    if hw.available_ram_gb >= total_required_gb:
        return HardwareFitVerdict(
            fits=True,
            recommended_device="cpu" if not hw.has_mps else "mps",
            estimated_ram_required_gb=total_required_gb,
            estimated_vram_required_gb=0.0,
            performance_tier="Good (System RAM)",
        )

    # Insufficient memory
    return HardwareFitVerdict(
        fits=False,
        recommended_device="cpu",
        estimated_ram_required_gb=total_required_gb,
        estimated_vram_required_gb=0.0,
        warning_message=f"Warning: Model requires ~{total_required_gb}GB RAM/VRAM, but only {hw.available_ram_gb}GB RAM is available.",
        performance_tier="Insufficient Memory (May OOM or Swap heavily)",
    )
