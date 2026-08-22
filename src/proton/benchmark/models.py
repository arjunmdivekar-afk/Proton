"""Data models for Proton Model & Provider Benchmark Suite."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestScore(BaseModel):
    name: str
    category: str
    passed: bool
    score: int = 100  # 0 to 100
    duration_ms: float = 0.0
    details: str = ""


class BenchmarkReport(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_id: str
    provider: str
    base_url: str
    latency_ms: float = 0.0
    ttft_ms: float = 0.0
    tokens_per_sec: float = 0.0
    total_tokens_generated: int = 0
    scores: List[TestScore] = Field(default_factory=list)
    overall_score: int = 0  # 0 to 100
    grade: str = "B"  # A+, A, B, C, D, F
    agent_readiness: str = "Agent Ready"
    recommendations: List[str] = Field(default_factory=list)
