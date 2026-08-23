"""API request and response schemas with rich Swagger UI examples for Proton Server."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Health & Info ---
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.6.4"
    uptime_seconds: float = 0.0
    workspace: str = ""
    active_connection: Optional[str] = None
    active_model: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "version": "2.6.4",
                "uptime_seconds": 124.5,
                "workspace": "C:\\Users\\arjun.divekar\\Desktop\\Proton",
                "active_connection": "server-1",
                "active_model": "llama-3.2-1b-instruct",
                "provider_type": "lmstudio",
                "base_url": "http://192.168.16.120:1234/v1",
            }
        }
    }


class ServerInfoResponse(BaseModel):
    name: str = "Proton Server"
    version: str = "2.6.4"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    endpoints: List[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Proton Autonomous AI Server",
                "version": "2.6.4",
                "docs_url": "/docs",
                "openapi_url": "/openapi.json",
                "endpoints": [
                    "POST /v1/chat",
                    "POST /v1/agents/run",
                    "POST /v1/tasks",
                    "GET  /v1/tasks",
                    "GET  /v1/graph/impact",
                ],
            }
        }
    }


# --- Chat & Streaming ---
class ChatMessage(BaseModel):
    role: str = Field(default="user", description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message text content")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "user",
                "content": "Explain how GraphRAG impact analysis calculates blast radius.",
            }
        }
    }


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Ordered list of conversation messages")
    model: Optional[str] = Field(default=None, description="Model ID override (optional)")
    stream: bool = Field(default=False, description="Enable Server-Sent Events (SSE) token streaming")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    session_id: Optional[str] = Field(default=None, description="Optional conversation session ID")
    use_rag: bool = Field(default=False, description="Augment context with vector RAG search")
    use_memory: bool = Field(default=True, description="Enrich system context with categorized memory")

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {"role": "user", "content": "How do I create a persistent task using the Proton API?"}
                ],
                "model": "llama-3.2-1b-instruct",
                "stream": True,
                "temperature": 0.7,
                "use_memory": True,
            }
        }
    }


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    role: str = "assistant"
    usage: Dict[str, Any] = Field(default_factory=dict)
    finish_reason: Optional[str] = "stop"
    duration_ms: float = 0.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "chatcmpl-a9f82d1c",
                "model": "llama-3.2-1b-instruct",
                "content": "You can create a persistent task by sending a POST request to `/v1/tasks` with a `title` and `goal` payload.",
                "role": "assistant",
                "usage": {"total_tokens": 34},
                "finish_reason": "stop",
                "duration_ms": 420.5,
            }
        }
    }


# --- Max-Level Agent ---
class AgentRunRequest(BaseModel):
    goal: str = Field(..., description="High-level engineering or refactoring goal")
    auto_approve: bool = Field(default=False, description="Run unattended in auto-approve mode")
    max_steps: int = Field(default=30, ge=1, le=100, description="Maximum turn steps allowed")
    workspace: Optional[str] = Field(default=None, description="Absolute path to target workspace")

    model_config = {
        "json_schema_extra": {
            "example": {
                "goal": "Refactor authentication middleware to support JWT validation and run test suite",
                "auto_approve": True,
                "max_steps": 30,
            }
        }
    }


class AgentRunResponse(BaseModel):
    goal: str
    status: str
    plan: List[str] = Field(default_factory=list)
    steps_executed: int = 0
    files_modified: List[str] = Field(default_factory=list)
    commands_executed: List[str] = Field(default_factory=list)
    tests_passed: bool = False
    audit_report_path: Optional[str] = None
    summary: str = ""
    duration_seconds: float = 0.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "goal": "Refactor authentication middleware to support JWT validation",
                "status": "COMPLETED",
                "plan": [
                    "Inspect existing auth module",
                    "Implement JWT signature validator",
                    "Run pytest suite",
                ],
                "steps_executed": 6,
                "files_modified": ["src/proton/auth/jwt.py", "tests/test_auth.py"],
                "commands_executed": ["pytest tests/test_auth.py"],
                "tests_passed": True,
                "audit_report_path": "C:\\Users\\arjun.divekar\\Desktop\\Proton\\.proton\\reports\\agent_report.md",
                "summary": "Successfully updated JWT validator and passed 8/8 unit tests.",
                "duration_seconds": 18.4,
            }
        }
    }


# --- Persistent Tasks ---
class TaskCreateRequest(BaseModel):
    title: str = Field(..., description="Short task title")
    goal: str = Field(..., description="Comprehensive task goal and specifications")
    auto_approve: bool = Field(default=False, description="Auto-approve non-destructive tool actions")
    max_steps: int = Field(default=30, description="Turn limit")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "ESP32 Camera Streaming Server",
                "goal": "Build an ESP32 web server that streams MJPEG video over WiFi on port 80",
                "auto_approve": False,
                "max_steps": 30,
            }
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "task-d30dbb25",
                "title": "ESP32 Camera Streaming Server",
                "goal": "Build an ESP32 web server that streams MJPEG video over WiFi on port 80",
                "status": "PENDING",
                "progress": 0,
                "plan": [
                    "Configure GPIO pins for OV2640 camera",
                    "Initialize WiFi station mode",
                    "Implement MJPEG stream handler",
                ],
                "files_modified": [],
                "commands_executed": [],
                "errors": [],
                "created_at": "2026-08-23 15:30:00",
                "updated_at": "2026-08-23 15:30:00",
            }
        }
    }


class TaskListResponse(BaseModel):
    total: int
    tasks: List[TaskResponse]


# --- Memory ---
class MemoryAddRequest(BaseModel):
    content: str = Field(..., description="Memory content description")
    memory_type: str = Field(
        default="PROJECT",
        description="Category: 'PROJECT', 'DECISION', 'PREFERENCE', 'FACT', 'TASK', 'USER', or 'SESSION'",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence rating")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "Always format Python code adhering to PEP 8 and include type annotations.",
                "memory_type": "PREFERENCE",
                "confidence": 1.0,
            }
        }
    }


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search keyword or semantic query")
    memory_type: Optional[str] = Field(default=None, description="Optional category filter")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results to return")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "PEP 8 formatting",
                "memory_type": "PREFERENCE",
                "limit": 5,
            }
        }
    }


class MemoryItemResponse(BaseModel):
    id: int
    content: str
    type: str
    confidence: float
    created_at: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "content": "Always format Python code adhering to PEP 8 and include type annotations.",
                "type": "PREFERENCE",
                "confidence": 1.0,
                "created_at": "2026-08-23 15:32:00",
            }
        }
    }


# --- GraphRAG ---
class GraphImpactRequest(BaseModel):
    symbol: str = Field(..., description="Target function, class, or method name to analyze")
    workspace: Optional[str] = Field(default=None, description="Optional workspace path")

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "validate_path",
            }
        }
    }


class GraphImpactResponse(BaseModel):
    symbol: str
    direct_callers: List[str] = Field(default_factory=list)
    indirect_callers: List[str] = Field(default_factory=list)
    tests_affected: List[str] = Field(default_factory=list)
    modules_impacted: List[str] = Field(default_factory=list)
    total_blast_radius: int = 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "validate_path",
                "direct_callers": ["read_file", "write_file", "edit_file", "list_directory"],
                "indirect_callers": ["ProtonMaxAgent.run", "TaskManager.run_task"],
                "tests_affected": ["tests/test_sandbox.py", "tests/test_security.py"],
                "modules_impacted": ["proton.tools.filesystem", "proton.agent.max_agent"],
                "total_blast_radius": 8,
            }
        }
    }


class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    functions: int
    classes: int
    modules: int
    tests: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_nodes": 595,
                "total_edges": 5045,
                "functions": 327,
                "classes": 151,
                "modules": 89,
                "tests": 28,
            }
        }
    }


# --- RAG ---
class RagSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Top matches to return")
    min_similarity: float = Field(default=0.2, ge=0.0, le=1.0, description="Minimum score threshold")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "hybrid vector BM25 similarity scoring",
                "top_k": 3,
                "min_similarity": 0.25,
            }
        }
    }


class RagSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "hybrid vector BM25 similarity scoring",
                "total": 1,
                "results": [
                    {
                        "chunk_id": "chunk-8f92ab11",
                        "doc_path": "src/proton/rag/hybrid_store.py",
                        "content": "def cosine_similarity(v1: List[float], v2: List[float]) -> float: ...",
                        "score": 0.88,
                        "citation": "src/proton/rag/hybrid_store.py:25-45",
                        "lines": "25-45",
                    }
                ],
            }
        }
    }


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

    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-08-23 15:35:00",
                "workspace": "C:\\Users\\arjun.divekar\\Desktop\\Proton",
                "total_checks": 8,
                "passed_checks": 8,
                "failed_checks": 0,
                "security_score": 100,
                "verdict": "Enterprise Secure",
                "checks": [
                    {
                        "name": "Path Traversal Defense",
                        "category": "Filesystem",
                        "passed": True,
                        "risk_mitigated": "Directory escapes",
                        "defense_layer": "FilesystemSandbox",
                        "details": "Blocked 5/5 path traversal sequences",
                    }
                ],
            }
        }
    }


# --- Tools ---
class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    risk_level: str


class ToolExecuteRequest(BaseModel):
    tool: str = Field(..., description="Tool name, e.g. 'read_file', 'shell_execute'")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Dictionary of arguments")
    workspace: Optional[str] = Field(default=None, description="Target workspace path")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tool": "read_file",
                "arguments": {"path": "pyproject.toml"},
            }
        }
    }


class ToolExecuteResponse(BaseModel):
    tool: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: float = 0.0

    model_config = {
        "json_schema_extra": {
            "example": {
                "tool": "read_file",
                "success": True,
                "result": "[project]\nname = \"proton-ai\"\nversion = \"2.6.4\"",
                "error": None,
                "duration_ms": 3.4,
            }
        }
    }


# --- Models & Providers ---
class ConnectionSwitchRequest(BaseModel):
    connection_id: str = Field(..., description="Target connection ID, e.g. 'server-1', 'default-lmstudio'")

    model_config = {
        "json_schema_extra": {
            "example": {
                "connection_id": "server-1",
            }
        }
    }


class ModelSwitchRequest(BaseModel):
    model_id: str = Field(..., description="Target model ID, e.g. 'llama-3.2-1b-instruct'")

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_id": "llama-3.2-1b-instruct",
            }
        }
    }
