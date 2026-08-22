"""Data models for Project Knowledge Graph (GraphRAG)."""

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    TEST = "TEST"
    VARIABLE = "VARIABLE"


class RelationType(str, Enum):
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    IMPORTS = "IMPORTS"
    DEFINES = "DEFINES"
    TESTS = "TESTS"
    REFERENCES = "REFERENCES"


class GraphNode(BaseModel):
    id: str  # Unique qualified identifier, e.g. "proton.security.sandbox.FilesystemSandbox.validate_path"
    name: str  # Short symbol name, e.g. "validate_path"
    node_type: NodeType
    file_path: str  # Relative workspace path
    line_number: int = 1
    docstring: Optional[str] = None
    signature: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation: RelationType
    line_number: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ImpactReport(BaseModel):
    target_symbol: str
    node_type: NodeType
    file_path: str
    direct_callers: List[str] = Field(default_factory=list)
    indirect_callers: List[str] = Field(default_factory=list)
    inheriting_classes: List[str] = Field(default_factory=list)
    importing_modules: List[str] = Field(default_factory=list)
    affecting_tests: List[str] = Field(default_factory=list)
    callees: List[str] = Field(default_factory=list)
    total_blast_radius: int = 0
    summary: str = ""


class GraphStats(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    modules_count: int = 0
    classes_count: int = 0
    functions_count: int = 0
    tests_count: int = 0
    calls_edges_count: int = 0
    inherits_edges_count: int = 0
    imports_edges_count: int = 0
    tests_edges_count: int = 0
