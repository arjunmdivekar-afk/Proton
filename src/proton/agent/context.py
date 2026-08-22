"""Context assembler that gathers system prompts, repo status, memory, and RAG."""

import os
from pathlib import Path
from typing import Dict, List, Optional

from datetime import datetime

from proton import __version__
from proton.core.types import Message, Role
from proton.memory.manager import MemoryManager, memory_manager
from proton.rag.pipeline import RAGPipeline


SYSTEM_PROMPT_TEMPLATE = """You are Proton (version {proton_version}), an enterprise-grade autonomous AI CLI assistant and coding agent.
You are running directly in the user's terminal environment with real-time access to executable tools and live system telemetry.
Your exact software version is {proton_version}. When asked for your version, state that you are Proton version {proton_version}.

CURRENT LIVE TIME & ENVIRONMENT:
- Current Date & Time: {current_datetime}
- Day of the Week: {day_of_week}
- Timezone: {timezone_info}
- When asked about the current time, date, today, or year, always provide this exact live time information accurately.

CAPABILITIES & TOOL USAGE:
- You have access to real tools: `read_file`, `write_file`, `edit_file`, `list_directory`, `search_code`, `shell_execute`, `git_status`, `git_diff`, `git_log`, `git_commit`, `apply_patch`, `run_tests`, `rag_search`, `duckduckgo_search`, `fetch_web_page`.
- When the user asks you to read, inspect, create, edit, or search files, check git, run tests, or execute commands: You MUST immediately invoke the corresponding tool function call.
- NEVER say "I cannot call tools" or "I cannot access files". You ARE directly authorized and empowered to execute tools to perform actions for the user.
- For conversational greetings, time questions, version queries, or general explanations: Respond directly in text without calling tools.

WORKSPACE CONTEXT:
- Working Directory: {workspace_path}
- Project Rules / Memory:
{memory_context}
"""


class ContextAssembler:
    """Builds token-budgeted context windows for LLM interactions."""

    def __init__(
        self,
        workspace_root: Path,
        memory_mgr: Optional[MemoryManager] = None,
        rag_pipeline: Optional[RAGPipeline] = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.memory_mgr = memory_mgr or memory_manager
        self.rag_pipeline = rag_pipeline

    def build_system_message(self, user_query: str = "") -> Message:
        # 1. Compute live datetime dynamically on every turn
        now = datetime.now().astimezone()
        current_datetime = now.strftime("%A, %B %d, %Y, %I:%M:%S %p")
        day_of_week = now.strftime("%A")
        tz_name = now.strftime("%Z") or "Local Time"
        tz_offset = now.strftime("%z")
        tz_formatted = f"UTC{tz_offset[:3]}:{tz_offset[3:]}" if tz_offset else "UTC"
        timezone_info = f"{tz_name} ({tz_formatted})"

        # 2. Recall relevant categorized memories
        memories = self.memory_mgr.recall(query=user_query) if user_query else self.memory_mgr.list_all()
        mem_lines = [f"- [{m.memory_type.value}] {m.content}" for m in memories[:8]]
        memory_str = "\n".join(mem_lines) if mem_lines else "None recorded yet."

        content = SYSTEM_PROMPT_TEMPLATE.format(
            proton_version=__version__,
            current_datetime=current_datetime,
            day_of_week=day_of_week,
            timezone_info=timezone_info,
            workspace_path=str(self.workspace_root),
            memory_context=memory_str,
        )
        return Message(role=Role.SYSTEM, content=content)

    async def augment_with_rag(self, query: str, top_k: int = 3) -> Optional[Message]:
        if not self.rag_pipeline:
            return None

        # Skip RAG search for short conversational queries or greetings
        q_clean = query.strip().lower()
        if len(q_clean.split()) <= 2 and q_clean in (
            "hello", "hi", "hey", "help", "test", "thanks", "thank you", "bye", "good morning", "good evening"
        ):
            return None

        results = await self.rag_pipeline.search(query=query, top_k=top_k)
        chunks_text = []
        if results:
            for r in results:
                chunks_text.append(f"--- Source {r.citation} (Score: {r.score}) ---\n{r.content}\n")

        # Check if query references symbols in Project Knowledge Graph
        try:
            from proton.graph.engine import ProjectGraphEngine
            from proton.graph.models import NodeType
            graph_engine = ProjectGraphEngine(self.workspace_root)
            words = [w.strip("(),.`'\"?:;") for w in query.split() if len(w) > 2]
            for w in words:
                node = graph_engine.resolve_symbol(w)
                if node and node.node_type != NodeType.MODULE:
                    rep = graph_engine.impact_analysis(w)
                    if rep.total_blast_radius > 0 or rep.callees or rep.affecting_tests:
                        graph_summary = (
                            f"\n--- PROJECT KNOWLEDGE GRAPH (GraphRAG) for `{node.name}` ({node.node_type.value} in `{node.file_path}`) ---\n"
                            f"• Direct Callers: {', '.join(rep.direct_callers) or 'None'}\n"
                            f"• Indirect Callers: {', '.join(rep.indirect_callers[:5]) or 'None'}\n"
                            f"• Subclasses: {', '.join(rep.inheriting_classes) or 'None'}\n"
                            f"• Automated Tests: {', '.join(rep.affecting_tests) or 'None'}\n"
                            f"• Calls Downstream: {', '.join(rep.callees[:6]) or 'None'}\n"
                            f"• Impact Summary: {rep.summary}\n"
                        )
                        chunks_text.append(graph_summary)
                        break
        except Exception:
            pass

        if not chunks_text:
            return None

        rag_prompt = (
            "RELEVANT PROJECT CONTEXT & KNOWLEDGE GRAPH (GraphRAG):\n"
            + "\n".join(chunks_text)
            + "\nUse the above verified context to answer accurately. Cite sources and relationship impact if applicable."
        )
        return Message(role=Role.SYSTEM, content=rag_prompt)
