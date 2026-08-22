"""Project Knowledge Graph Engine with SQLite persistence and Impact Analysis."""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque

from proton.core.config import get_proton_home
from proton.graph.models import (
    GraphNode,
    GraphEdge,
    NodeType,
    RelationType,
    ImpactReport,
    GraphStats,
)
from proton.graph.extractor import CodeGraphExtractor


class ProjectGraphEngine:
    """High-performance Knowledge Graph Engine for code dependency and impact analysis."""

    def __init__(self, workspace_root: Optional[Path] = None, db_path: Optional[Path] = None) -> None:
        self.workspace = (workspace_root or Path.cwd()).resolve()
        self.db_path = db_path or (get_proton_home() / "knowledge" / "graph.db")
        self.nodes: Dict[str, GraphNode] = {}
        self.nodes_by_name: Dict[str, List[GraphNode]] = defaultdict(list)
        self.adj_out: Dict[str, List[Tuple[str, RelationType]]] = defaultdict(list)
        self.adj_in: Dict[str, List[Tuple[str, RelationType]]] = defaultdict(list)
        self._init_db()
        self.load_graph_from_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER,
                    docstring TEXT,
                    signature TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS graph_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    line_number INTEGER,
                    metadata_json TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_node_name ON graph_nodes(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edge_source ON graph_edges(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edge_target ON graph_edges(target_id)")
            conn.commit()

    def build_graph(self) -> GraphStats:
        """Scan workspace AST, extract nodes/edges, and persist to SQLite."""
        extractor = CodeGraphExtractor(self.workspace)
        nodes, edges = extractor.extract_graph()

        # Clear existing workspace records
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM graph_edges")
            conn.execute("DELETE FROM graph_nodes")
            
            # Insert nodes
            for n in nodes:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO graph_nodes (id, name, node_type, file_path, line_number, docstring, signature, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (n.id, n.name, n.node_type.value, n.file_path, n.line_number, n.docstring, n.signature, "{}")
                )
                
            # Insert edges
            for e in edges:
                conn.execute(
                    """
                    INSERT INTO graph_edges (source_id, target_id, relation, line_number, metadata_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (e.source_id, e.target_id, e.relation.value, e.line_number, "{}")
                )
            conn.commit()

        self.load_graph_from_db()
        return self.get_stats()

    def load_graph_from_db(self) -> None:
        """Load in-memory index structures from SQLite database."""
        self.nodes.clear()
        self.nodes_by_name.clear()
        self.adj_out.clear()
        self.adj_in.clear()

        if not self.db_path.exists():
            return

        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, node_type, file_path, line_number, docstring, signature, metadata_json FROM graph_nodes")
            for r in cur.fetchall():
                node = GraphNode(
                    id=r[0],
                    name=r[1],
                    node_type=NodeType(r[2]),
                    file_path=r[3],
                    line_number=r[4] or 1,
                    docstring=r[5],
                    signature=r[6],
                )
                self.nodes[node.id] = node
                self.nodes_by_name[node.name.lower()].append(node)

            cur.execute("SELECT source_id, target_id, relation FROM graph_edges")
            for r in cur.fetchall():
                src, tgt, rel = r[0], r[1], RelationType(r[2])
                self.adj_out[src].append((tgt, rel))
                self.adj_in[tgt].append((src, rel))

    def resolve_symbol(self, symbol: str) -> Optional[GraphNode]:
        """Resolve a symbol string to the best matching GraphNode."""
        clean = symbol.strip()
        # Exact ID match
        if clean in self.nodes:
            return self.nodes[clean]

        # Case-insensitive name match
        lower_name = clean.lower()
        if lower_name in self.nodes_by_name:
            # Return first non-test node if possible
            matches = self.nodes_by_name[lower_name]
            for m in matches:
                if m.node_type != NodeType.TEST:
                    return m
            return matches[0]

        # Suffix / partial match
        for node_id, node in self.nodes.items():
            if node_id.endswith(f".{clean}") or f".{clean}." in node_id:
                return node
        return None

    def impact_analysis(self, symbol: str) -> ImpactReport:
        """Calculate the blast radius and downstream/upstream effects of modifying a symbol."""
        node = self.resolve_symbol(symbol)
        if not node:
            return ImpactReport(
                target_symbol=symbol,
                node_type=NodeType.FUNCTION,
                file_path="Unknown",
                summary=f"Symbol '{symbol}' was not found in the project graph. Run `proton graph build` to index.",
            )

        direct_callers: Set[str] = set()
        indirect_callers: Set[str] = set()
        inheriting_classes: Set[str] = set()
        importing_modules: Set[str] = set()
        affecting_tests: Set[str] = set()
        callees: Set[str] = set()

        # 1. Inspect direct callers & importers
        # Match incoming edges targeting qualified node.id OR short node.name
        targets_to_check = {node.id, node.name}
        for tgt in targets_to_check:
            for src, rel in self.adj_in.get(tgt, []):
                if rel == RelationType.CALLS:
                    direct_callers.add(src)
                elif rel == RelationType.INHERITS:
                    inheriting_classes.add(src)
                elif rel == RelationType.IMPORTS:
                    importing_modules.add(src)
                elif rel == RelationType.TESTS:
                    affecting_tests.add(src)

        # 2. Inspect outgoing callees (what this function calls)
        for tgt, rel in self.adj_out.get(node.id, []):
            if rel == RelationType.CALLS:
                callees.add(tgt)

        # 3. BFS traversal to discover 2nd and 3rd degree indirect callers & tests
        queue = deque([(caller, 1) for caller in direct_callers])
        visited = set(direct_callers)
        while queue:
            curr, depth = queue.popleft()
            if depth >= 3:
                continue
            curr_node = self.resolve_symbol(curr)
            curr_targets = {curr, curr_node.name if curr_node else curr}
            for ct in curr_targets:
                for parent_src, rel in self.adj_in.get(ct, []):
                    if rel == RelationType.CALLS and parent_src not in visited:
                        visited.add(parent_src)
                        indirect_callers.add(parent_src)
                        queue.append((parent_src, depth + 1))
                    elif rel == RelationType.TESTS:
                        affecting_tests.add(parent_src)

        # Total blast radius
        total_blast = len(direct_callers) + len(indirect_callers) + len(inheriting_classes) + len(affecting_tests)

        # Generate summary
        summary_parts = [
            f"Modifying `{node.name}` ({node.node_type.value} in `{node.file_path}:{node.line_number}`) directly affects {len(direct_callers)} caller(s) and {len(affecting_tests)} test suite(s)."
        ]
        if inheriting_classes:
            summary_parts.append(f"Subclasses affected: {', '.join(list(inheriting_classes)[:3])}")
        if affecting_tests:
            summary_parts.append(f"Automated tests to run for verification: {', '.join(list(affecting_tests)[:4])}")

        return ImpactReport(
            target_symbol=node.id,
            node_type=node.node_type,
            file_path=f"{node.file_path}:{node.line_number}",
            direct_callers=sorted(list(direct_callers)),
            indirect_callers=sorted(list(indirect_callers)),
            inheriting_classes=sorted(list(inheriting_classes)),
            importing_modules=sorted(list(importing_modules)),
            affecting_tests=sorted(list(affecting_tests)),
            callees=sorted(list(callees)),
            total_blast_radius=total_blast,
            summary=" ".join(summary_parts),
        )

    def get_stats(self) -> GraphStats:
        """Compute summary statistics for the project knowledge graph."""
        mod_c = sum(1 for n in self.nodes.values() if n.node_type == NodeType.MODULE)
        cls_c = sum(1 for n in self.nodes.values() if n.node_type == NodeType.CLASS)
        fn_c = sum(1 for n in self.nodes.values() if n.node_type in (NodeType.FUNCTION, NodeType.METHOD))
        test_c = sum(1 for n in self.nodes.values() if n.node_type == NodeType.TEST)

        calls_c = 0
        inherits_c = 0
        imports_c = 0
        tests_c = 0
        total_edges = 0

        for edges_list in self.adj_out.values():
            total_edges += len(edges_list)
            for _, rel in edges_list:
                if rel == RelationType.CALLS:
                    calls_c += 1
                elif rel == RelationType.INHERITS:
                    inherits_c += 1
                elif rel == RelationType.IMPORTS:
                    imports_c += 1
                elif rel == RelationType.TESTS:
                    tests_c += 1

        return GraphStats(
            total_nodes=len(self.nodes),
            total_edges=total_edges,
            modules_count=mod_c,
            classes_count=cls_c,
            functions_count=fn_c,
            tests_count=test_c,
            calls_edges_count=calls_c,
            inherits_edges_count=inherits_c,
            imports_edges_count=imports_c,
            tests_edges_count=tests_c,
        )
