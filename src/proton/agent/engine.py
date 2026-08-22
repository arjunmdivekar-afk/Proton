import asyncio
import json
import re
from typing import AsyncGenerator, Dict, List, Optional, Any, Set
from pydantic import BaseModel

from proton.core.types import Message, Role, ToolCall, ToolResult
from proton.providers.base import ModelProvider, StreamChunk
from proton.tools.registry import ToolRegistry
from proton.agent.context import ContextAssembler
from proton.agent.planner import Plan, PlanStep, StepStatus
from proton.core.events import event_bus, Event, EventType
from proton.core.exceptions import ProtonException, ProviderError


def extract_text_tool_calls(text: str, registered_names: Set[str]) -> List[ToolCall]:
    """Extract tool calls emitted as text/markdown/XML/JSON by models lacking native tool tokens."""
    calls: List[ToolCall] = []

    def _try_parse_tool_dict(data: Any) -> Optional[ToolCall]:
        if not isinstance(data, dict):
            return None

        name = None
        args: Any = {}

        # If nested under "function" (dict)
        if isinstance(data.get("function"), dict):
            fn = data["function"]
            name = fn.get("name")
            args = fn.get("parameters") or fn.get("arguments") or {}
        # If nested under "function" (string)
        elif isinstance(data.get("function"), str):
            name = data.get("function")
            args = data.get("parameters") or data.get("arguments") or {}
        # Direct name/tool/action
        elif isinstance(data.get("name"), str):
            name = data.get("name")
            args = data.get("arguments") or data.get("parameters") or {k: v for k, v in data.items() if k not in ("name", "arguments", "parameters")}
        elif isinstance(data.get("tool"), str):
            name = data.get("tool")
            args = data.get("arguments") or data.get("parameters") or {k: v for k, v in data.items() if k not in ("tool", "arguments", "parameters")}
        elif isinstance(data.get("action"), str):
            name = data.get("action")
            args = data.get("action_input") or data.get("arguments") or {}

        if isinstance(name, str) and name.strip() in registered_names:
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}
            elif not isinstance(args, dict):
                args = {"value": args}
            return ToolCall(id=f"call_{len(calls)}", name=name.strip(), arguments=args)
        return None

    # Pattern 1: <tool_call> ... </tool_call>
    xml_matches = re.findall(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
    for block in xml_matches:
        try:
            data = json.loads(block.strip())
            tc = _try_parse_tool_dict(data)
            if tc:
                calls.append(tc)
        except Exception:
            pass

    # Pattern 2: ```json ... ``` or ``` ... ``` code blocks
    if not calls:
        code_blocks = re.findall(r"```(?:json|bash)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        for block in code_blocks:
            try:
                data = json.loads(block.strip())
                tc = _try_parse_tool_dict(data)
                if tc:
                    calls.append(tc)
            except Exception:
                pass

    # Pattern 3: Standalone JSON object in text
    if not calls:
        raw_json_objs = re.findall(r"(\{\s*\"(?:name|type|function|tool|action)\"\s*:.*?\})", text, re.DOTALL)
        for block in raw_json_objs:
            try:
                data = json.loads(block.strip())
                tc = _try_parse_tool_dict(data)
                if tc:
                    calls.append(tc)
            except Exception:
                pass

    return calls


class AgentResult(BaseModel):
    final_response: str
    messages: List[Message]
    tool_calls_executed: int
    steps_taken: int
    success: bool
    error: Optional[str] = None


def is_conversational_prompt(prompt: str) -> bool:
    """Detect if a user prompt is asking for code/explanations/chat and should skip tool schemas."""
    p = prompt.strip().lower()

    # Informational, time, and code-writing requests (should answer directly without external tools)
    info_code_patterns = [
        r"^(what\s+time\s+is\s+it|what\s+is\s+the\s+time|current\s+time|tell\s+me\s+the\s+time|time\s+now|time\s+please)\b",
        r"^(what\s+is\s+today'?s\s+date|what\s+is\s+the\s+date|what\s+date\s+is\s+it|what\s+day\s+is\s+today|what\s+year\s+is\s+it|today'?s\s+date|date\s+today)\b",
        r"^(give\s+me|show\s+me|write\s+me|generate|provide)\s+(the\s+)?(code|full\s+code|example|snippet|script|html|css|js|javascript|python|function|page)\b",
        r"^(how\s+to|how\s+do\s+i|how\s+can\s+i)\s+(make|create|write|build|code|implement|do)\b",
        r"^(what\s+is|explain|describe|tell\s+me\s+about|can\s+you\s+write|can\s+you\s+explain|can\s+you\s+give)\b",
        r"^(hi|hello|hey|hola|greetings|howdy|sup|yo|good\s+morning|good\s+evening)\b",
        r"^(who\s+are\s+you|what\s+can\s+you\s+do|help|thanks|thank\s+you|bye|goodbye|ok|okay|cool|nice|ping|test)\b",
    ]
    for pattern in info_code_patterns:
        if re.search(pattern, p):
            return True

    # Explicit tool action keywords (when user asks agent to execute actions on workspace/web)
    tool_action_keywords = {
        "git", "commit", "diff", "branch", "checkout", "push", "pull",
        "terminal", "bash", "powershell", "cmd",
        "test", "pytest", "npm", "pip", "patch",
        "rag", "index", "doctor", "duckduckgo"
    }
    words = set(re.findall(r"\b\w+\b", p))
    if words & tool_action_keywords:
        return False

    # Check for explicit web search requests
    if re.search(r"\b(search\s+the\s+web|search\s+web|web\s+search|search\s+online|search\s+duckduckgo|lookup\s+online|google)\b", p):
        return False

    # Check for explicit file operations on disk (e.g. "save to file", "edit file.py", "read file")
    if re.search(r"\b(edit|modify|save\s+to|write\s+to|delete|remove)\s+(the\s+)?(file|\.|\/|[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)\b", p):
        return False
    if re.search(r"\b(run|execute)\s+(command|script|tests|build)\b", p):
        return False
    if re.search(r"\b(search|grep|find)\s+(in\s+files|codebase|repo|directory)\b", p):
        return False

    # Otherwise default to direct conversational / code answer
    return True


class AgentEngine:
    """Core autonomous agent loop with multi-step tool execution and streaming."""

    def __init__(
        self,
        provider: ModelProvider,
        tool_registry: ToolRegistry,
        context_assembler: ContextAssembler,
        model_name: str,
        max_steps: int = 30,
    ) -> None:
        self.provider = provider
        self.tool_registry = tool_registry
        self.context_assembler = context_assembler
        self.model_name = model_name
        self.max_steps = max_steps
        self.last_usage: Optional[Dict[str, int]] = None

    async def run(
        self,
        user_input: str,
        history: Optional[List[Message]] = None,
        session_id: Optional[str] = None,
        use_rag: bool = True,
    ) -> AgentResult:
        """Run non-streaming agent turn."""
        full_response = ""
        tool_calls_count = 0
        async for chunk in self.stream_run(
            user_input=user_input,
            history=history,
            session_id=session_id,
            use_rag=use_rag,
        ):
            if isinstance(chunk, str):
                full_response += chunk

        return AgentResult(
            final_response=full_response,
            messages=[],
            tool_calls_executed=tool_calls_count,
            steps_taken=1,
            success=True,
        )

    async def stream_run(
        self,
        user_input: str,
        history: Optional[List[Message]] = None,
        session_id: Optional[str] = None,
        use_rag: bool = True,
        disable_tools: bool = False,
        force_tools: bool = False,
    ) -> AsyncGenerator[Any, None]:
        """Stream assistant tokens and tool events step by step."""
        messages: List[Message] = []

        # 1. System prompt & memory
        system_msg = self.context_assembler.build_system_message(user_input)
        if force_tools:
            system_msg.content += (
                "\n\nIMPORTANT: You are operating in Autonomous Agent Mode. You have full permission and capabilities "
                "to create files, edit files, and execute shell commands using your available tools. "
                "You MUST use tools (e.g. `write_file`, `edit_file`, `shell_execute`, `read_file`, `search_code`) to perform "
                "the requested task. Never refuse execution; always call the appropriate tool."
            )
        messages.append(system_msg)

        # 2. RAG context augmentation if enabled
        if use_rag:
            rag_msg = await self.context_assembler.augment_with_rag(user_input)
            if rag_msg:
                messages.append(rag_msg)

        # 3. Add existing conversation history
        if history:
            messages.extend(history)

        # 4. User message
        messages.append(Message(role=Role.USER, content=user_input))

        await event_bus.emit(
            Event(type=EventType.AGENT_STARTED, data={"prompt": user_input}, session_id=session_id)
        )

        # Gating: Do not pass tool schemas for conversational greetings/chat or when disabled (unless force_tools is True)
        is_chat_only = (is_conversational_prompt(user_input) and not force_tools) or disable_tools
        all_schemas = self.tool_registry.get_schemas()
        active_tools = None if is_chat_only else (all_schemas if all_schemas else None)

        step = 0
        total_tool_calls = 0

        while step < self.max_steps:
            step += 1
            step_content = ""
            active_tool_calls: List[ToolCall] = []

            # Stream response from model provider
            try:
                async for chunk in self.provider.stream_chat(
                    messages=messages,
                    model=self.model_name,
                    tools=active_tools,
                ):
                    if chunk.usage:
                        self.last_usage = chunk.usage

                    if chunk.delta:
                        step_content += chunk.delta
                        yield chunk.delta

                    if chunk.tool_calls:
                        active_tool_calls.extend(chunk.tool_calls)

            except Exception as e:
                err_text = f"\n[Model Provider Error: {e}]"
                yield err_text
                await event_bus.emit(
                    Event(type=EventType.AGENT_ERROR, data={"error": str(e)}, session_id=session_id)
                )
                return

            # If initial stream with tools produced empty content and no tool calls,
            # retry without tools in case the model does not support tool schemas.
            if step == 1 and not step_content.strip() and not active_tool_calls and active_tools:
                try:
                    async for chunk in self.provider.stream_chat(
                        messages=messages,
                        model=self.model_name,
                        tools=None,
                    ):
                        if chunk.delta:
                            step_content += chunk.delta
                            yield chunk.delta
                except Exception:
                    pass

            # If streaming still produced no content, fallback to non-streaming chat_complete
            if step == 1 and not step_content.strip() and not active_tool_calls:
                try:
                    chat_resp = await self.provider.chat_complete(
                        messages=messages,
                        model=self.model_name,
                        tools=None,
                    )
                    if chat_resp.content:
                        step_content = chat_resp.content
                        yield chat_resp.content
                except Exception:
                    pass

            # If no API tool calls received, check if the model output a text-based tool call (e.g. <tool_call> or markdown json)
            if not active_tool_calls and step_content.strip():
                registered_names = set(self.tool_registry._tools.keys())
                text_calls = extract_text_tool_calls(step_content, registered_names)
                if text_calls:
                    active_tool_calls.extend(text_calls)

            # Filter active tool calls strictly to registered tools with non-empty names
            active_tool_calls = [
                tc for tc in active_tool_calls
                if tc.name and self.tool_registry.get_tool(tc.name) is not None
            ]

            # Append assistant's partial or full response
            assistant_msg = Message(
                role=Role.ASSISTANT,
                content=step_content,
                tool_calls=[tc.model_dump() for tc in active_tool_calls] if active_tool_calls else None,
            )
            messages.append(assistant_msg)

            # If no valid tools requested by model, finish turn!
            if not active_tool_calls:
                break

            # Execute tool calls
            for tc in active_tool_calls:
                total_tool_calls += 1
                yield f"\n[bold cyan]● Executing tool:[/bold cyan] `{tc.name}`\n"

                result = await self.tool_registry.execute(
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    tool_call_id=tc.id,
                    session_id=session_id,
                )

                res_content = str(result.data) if result.success else f"Error: {result.error}"
                yield f"[dim]✓ Finished {tc.name} ({result.duration_ms:.1f}ms)[/dim]\n\n"

                # Append tool result to context
                messages.append(
                    Message(
                        role=Role.TOOL,
                        name=tc.name,
                        content=res_content,
                        tool_call_id=tc.id,
                    )
                )

        await event_bus.emit(
            Event(
                type=EventType.AGENT_COMPLETED,
                data={"total_steps": step, "total_tool_calls": total_tool_calls},
                session_id=session_id,
            )
        )
