"""Data models for Proton Repository & Codebase Inspection."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LanguageInfo(BaseModel):
    name: str
    files_count: int = 0
    lines_of_code: int = 0
    percentage: float = 0.0


class FrameworkInfo(BaseModel):
    name: str
    category: str  # e.g. "Web Framework", "TUI / CLI", "Data / AI", "Testing"
    confidence: str = "High"


class DependencyItem(BaseModel):
    name: str
    version_spec: str = ""
    is_dev: bool = False


class DependencyReport(BaseModel):
    package_manager: str = "Unknown"
    manifest_files: List[str] = Field(default_factory=list)
    direct_dependencies: List[DependencyItem] = Field(default_factory=list)
    total_count: int = 0


class ProblemItem(BaseModel):
    severity: str  # "HIGH", "MEDIUM", "LOW", "INFO"
    title: str
    description: str
    file_path: Optional[str] = None


class SecurityAuditReport(BaseModel):
    score: int = 100
    hardcoded_secrets_found: List[str] = Field(default_factory=list)
    vulnerabilities: List[ProblemItem] = Field(default_factory=list)
    security_files: List[str] = Field(default_factory=list)


class TestAuditReport(BaseModel):
    framework: str = "None"
    test_files_count: int = 0
    test_directories: List[str] = Field(default_factory=list)
    has_ci_config: bool = False
    estimated_coverage: str = "Unknown"


class PerformanceReport(BaseModel):
    large_files: List[Dict[str, Any]] = Field(default_factory=list)
    total_repo_size_mb: float = 0.0
    bottlenecks: List[str] = Field(default_factory=list)


class ArchitectureReport(BaseModel):
    pattern: str = "Standard Modular"
    entry_points: List[str] = Field(default_factory=list)
    core_modules: List[str] = Field(default_factory=list)
    layers: List[str] = Field(default_factory=list)


class FullInspectionReport(BaseModel):
    project_name: str
    workspace_root: str
    languages: List[LanguageInfo] = Field(default_factory=list)
    frameworks: List[FrameworkInfo] = Field(default_factory=list)
    dependencies: DependencyReport = Field(default_factory=DependencyReport)
    architecture: ArchitectureReport = Field(default_factory=ArchitectureReport)
    entry_points: List[str] = Field(default_factory=list)
    test_framework: TestAuditReport = Field(default_factory=TestAuditReport)
    git_status: Dict[str, Any] = Field(default_factory=dict)
    documentation: List[str] = Field(default_factory=list)
    environment: Dict[str, Any] = Field(default_factory=dict)
    potential_problems: List[ProblemItem] = Field(default_factory=list)
    security: SecurityAuditReport = Field(default_factory=SecurityAuditReport)
    performance: PerformanceReport = Field(default_factory=PerformanceReport)
