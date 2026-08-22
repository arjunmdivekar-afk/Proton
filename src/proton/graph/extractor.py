"""AST-based static code analyzer extracting nodes and relationship edges for GraphRAG."""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from proton.graph.models import GraphNode, GraphEdge, NodeType, RelationType

IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules", "dist", "build",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "target", ".idea", ".vscode",
    ".gemini", ".next", ".nuxt", "coverage", ".turbo", "egg-info"
}


class ASTGraphVisitor(ast.NodeVisitor):
    """Visits Python AST nodes to extract functions, classes, calls, imports, and inheritance."""

    def __init__(self, file_rel_path: str, module_name: str) -> None:
        self.file_path = file_rel_path
        self.module_name = module_name
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.is_test_file = "test" in file_rel_path.lower()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.edges.append(
                GraphEdge(
                    source_id=self.module_name,
                    target_id=alias.name,
                    relation=RelationType.IMPORTS,
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        for alias in node.names:
            target = f"{mod}.{alias.name}" if mod else alias.name
            self.edges.append(
                GraphEdge(
                    source_id=self.module_name,
                    target_id=target,
                    relation=RelationType.IMPORTS,
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_id = f"{self.module_name}.{node.name}"
        doc = ast.get_docstring(node)
        self.nodes.append(
            GraphNode(
                id=class_id,
                name=node.name,
                node_type=NodeType.CLASS,
                file_path=self.file_path,
                line_number=node.lineno,
                docstring=doc,
            )
        )
        self.edges.append(
            GraphEdge(
                source_id=self.module_name,
                target_id=class_id,
                relation=RelationType.DEFINES,
                line_number=node.lineno,
            )
        )

        # Inheritance relationships
        for base in node.bases:
            base_name = None
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = f"{getattr(base.value, 'id', '')}.{base.attr}"
            if base_name:
                self.edges.append(
                    GraphEdge(
                        source_id=class_id,
                        target_id=base_name,
                        relation=RelationType.INHERITS,
                        line_number=node.lineno,
                    )
                )

        prev_class = self.current_class
        self.current_class = class_id
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node) -> None:
        is_test = self.is_test_file or node.name.startswith("test_")
        if self.current_class:
            func_id = f"{self.current_class}.{node.name}"
            node_type = NodeType.TEST if is_test else NodeType.METHOD
            parent_id = self.current_class
        else:
            func_id = f"{self.module_name}.{node.name}"
            node_type = NodeType.TEST if is_test else NodeType.FUNCTION
            parent_id = self.module_name

        doc = ast.get_docstring(node)
        # Extract signature parameters
        args = [a.arg for a in node.args.args]
        sig = f"({', '.join(args)})"

        self.nodes.append(
            GraphNode(
                id=func_id,
                name=node.name,
                node_type=node_type,
                file_path=self.file_path,
                line_number=node.lineno,
                docstring=doc,
                signature=sig,
            )
        )
        self.edges.append(
            GraphEdge(
                source_id=parent_id,
                target_id=func_id,
                relation=RelationType.DEFINES,
                line_number=node.lineno,
            )
        )

        prev_func = self.current_function
        self.current_function = func_id
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Call(self, node: ast.Call) -> None:
        if self.current_function:
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr

            if callee_name and not callee_name.startswith("__"):
                rel = RelationType.TESTS if self.is_test_file or "test_" in self.current_function else RelationType.CALLS
                self.edges.append(
                    GraphEdge(
                        source_id=self.current_function,
                        target_id=callee_name,
                        relation=rel,
                        line_number=node.lineno,
                    )
                )
        self.generic_visit(node)


class CodeGraphExtractor:
    """Scans and extracts symbols and relationships across workspace repositories."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace = workspace_root.resolve()

    def extract_graph(self) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Extract all nodes and edges from Python source tree."""
        all_nodes: List[GraphNode] = []
        all_edges: List[GraphEdge] = []

        for root, dirs, files in os.walk(self.workspace):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.endswith(".egg-info")]
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(self.workspace)).replace("\\", "/")
                    module_name = rel_path.replace("/", ".").replace(".py", "")
                    if module_name.startswith("src."):
                        module_name = module_name[4:]

                    # Add Module node
                    mod_node = GraphNode(
                        id=module_name,
                        name=file_path.stem,
                        node_type=NodeType.MODULE,
                        file_path=rel_path,
                        line_number=1,
                    )
                    all_nodes.append(mod_node)

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        parsed = ast.parse(content, filename=str(file_path))
                        visitor = ASTGraphVisitor(rel_path, module_name)
                        visitor.visit(parsed)
                        all_nodes.extend(visitor.nodes)
                        all_edges.extend(visitor.edges)
                    except Exception:
                        continue

        return all_nodes, all_edges
