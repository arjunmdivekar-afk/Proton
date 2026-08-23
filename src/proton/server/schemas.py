"""API request and response schemas for Proton Server."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Health & Info ---
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.4.4"
    uptime_seconds: float = 0.0
    workspace: str = ""
    active_connection: Optional[str] = None
    active_model: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None


class ServerInfoResponse(BaseModel):
    name: str = "Proton Server"
    version: str = "2.4.4"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    endpoints: List[str] = Field(default_factory=list)


# --- Chat & Streaming ---
class ChatMessage(BaseModel):
    role: str = "user"  # system, user, assistant
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    session_id: Optional[str] = None
    use_rag: bool = False
    use_memory: bool = True


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    role: str = "assistant"
    usage: Dict[str, Any] = Field(default_factory=dict)
    finish_reason: Optional[str] = "stop"
    duration_ms: float = 0.0


# --- Max-Level Agent ---
class AgentRunRequest(BaseModel):
    goal: str
    auto_approve: bool = False
    max_steps: int = 30
    workspace: Optional[str] = None


class AgentRunResponse(BaseModel):
    goal: str
    status: str  # COMPLETED, FAILED, RUNNING
    plan: List[str] = Field(default_factory=list)
    steps_executed: int = 0
    files_modified: List[str] = Field(default_factory=list)
    commands_executed: List[str] = Field(default_factory=list)
    tests_passed: bool = False
    audit_report_path: Optional[str] = None
    summary: str = ""
    duration_seconds: float = 0.0


# --- Persistent Tasks ---
class TaskCreateRequest(BaseModel):
    title: str
    goal: str
    auto_approve: bool = False
    max_steps: int = 30


class TaskResponse(BaseModel):
    id: str
    title: str
    goal: str
    status: str
    progress: int = 0
    plan: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    commands_executed: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    total: int
    tasks: List[TaskResponse]


# --- Memory ---
class MemoryAddRequest(BaseModel):
    content: str
    memory_type: str = "PROJECT"  # PROJECT, DECISION, PREFERENCE, FACT, TASK, USER, SESSION
    confidence: float = 1.0


class MemorySearchRequest(BaseModel):
    query: str
    memory_type: Optional[str] = None
    limit: int = 10


class MemoryItemResponse(BaseModel):
    id: int
    content: str
    type: str
    confidence: float
    created_at: str


# --- GraphRAG ---
class GraphImpactRequest(BaseModel):
    symbol: str
    workspace: Optional[str] = None


class GraphImpactResponse(BaseModel):
    symbol: str
    direct_callers: List[str] = Field(default_factory=list)
    indirect_callers: List[str] = Field(default_factory=list)
    tests_affected: List[str] = Field(default_factory=list)
    modules_impacted: List[str] = Field(default_factory=list)
    total_blast_radius: int = 0


class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    functions: int
    classes: int
    modules: int
    tests: int


# --- RAG ---
class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    min_similarity: float = 0.2


class RagSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0


# --- Security ---
class SecurityCheckResponse(BaseModel):
    name: str
    category: str
    passed: bool
    risk_mitigated: str
    defense_layer: str
    details: str = ""


class SecurityVerificationResponse(BaseModel):
    timestamp: str
    workspace: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    security_score: int
    verdict: str
    checks: List[SecurityCheckResponse]


# --- Tools ---
class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    risk_level: str


class ToolExecuteRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    workspace: Optional[str] = None


class ToolExecuteResponse(BaseModel):
    tool: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: float = 0.0


# --- Models & Providers ---
class ConnectionSwitchRequest(BaseModel):
    connection_id: str


class ModelSwitchRequest(BaseModel):
    model_id: str
