"""Central Tool Registry for registering, validating, and executing tools."""

import time
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from proton.tools.base import BaseTool
from proton.core.types import ToolResult, RiskLevel
from proton.security.policy import PolicyEngine
from proton.security.approval import ApprovalManager
from proton.security.audit import audit_logger
from proton.core.events import event_bus, Event, EventType
from proton.core.exceptions import SecurityError, ApprovalDeniedError


class ToolRegistry:
    """Central registry and executor for deterministic tools."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        approval_manager: Optional[ApprovalManager] = None,
    ) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self.policy_engine = policy_engine or PolicyEngine()
        self.approval_manager = approval_manager or ApprovalManager()

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get(self, name: str, default: Optional[BaseTool] = None) -> Optional[BaseTool]:
        return self._tools.get(name, default)

    def __getitem__(self, name: str) -> BaseTool:
        return self._tools[name]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-format schemas for all registered tools."""
        return [tool.get_json_schema() for tool in self._tools.values()]

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_call_id: str = "call_0",
        session_id: Optional[str] = None,
    ) -> ToolResult:
        """Validate, evaluate approval policy, execute, and record audit log."""
        t_start = time.perf_counter()
        tool = self.get_tool(tool_name)

        if not tool:
            err_msg = f"Tool '{tool_name}' is not registered."
            return ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=False,
                error=err_msg,
                duration_ms=0.0,
            )

        # 1. Validate arguments against Pydantic schema
        validated_args = arguments
        if tool.args_schema:
            try:
                model_inst = tool.args_schema(**arguments)
                validated_args = model_inst.model_dump()
            except ValidationError as ve:
                err_msg = f"Invalid arguments for tool '{tool_name}': {ve}"
                return ToolResult(
                    tool_call_id=tool_call_id,
                    name=tool_name,
                    success=False,
                    error=err_msg,
                    duration_ms=0.0,
                )

        # 2. Determine Risk Level
        risk = self.policy_engine.get_tool_risk(tool_name, validated_args)

        # 3. Request Human Approval if required
        try:
            await self.approval_manager.request_approval(tool_name, validated_args, risk)
        except ApprovalDeniedError as ade:
            audit_logger.log(
                event_type="tool.denied",
                session_id=session_id,
                tool_name=tool_name,
                risk_level=risk.value,
                decision="deny",
                details=validated_args,
            )
            return ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=False,
                error=f"Execution denied by user: {ade}",
                duration_ms=round((time.perf_counter() - t_start) * 1000.0, 2),
            )

        # 4. Emit execution start event
        await event_bus.emit(
            Event(
                type=EventType.TOOL_STARTED,
                data={"tool": tool_name, "arguments": validated_args, "call_id": tool_call_id},
                session_id=session_id,
            )
        )

        # 5. Execute Tool
        try:
            raw_result = await tool.run(**validated_args)
            duration_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            
            # Check if dict return contains explicit error
            is_error = isinstance(raw_result, dict) and "error" in raw_result
            err = raw_result.get("error") if is_error else None

            result = ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=not is_error,
                data=raw_result if not is_error else None,
                error=err,
                duration_ms=duration_ms,
            )

            # Audit
            audit_logger.log(
                event_type="tool.executed",
                session_id=session_id,
                tool_name=tool_name,
                risk_level=risk.value,
                decision="allow",
                details={"args": validated_args, "duration_ms": duration_ms, "success": result.success},
            )

            # Emit completion event
            await event_bus.emit(
                Event(
                    type=EventType.TOOL_COMPLETED,
                    data={"tool": tool_name, "success": result.success, "duration_ms": duration_ms},
                    session_id=session_id,
                )
            )
            return result

        except Exception as e:
            duration_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            audit_logger.log(
                event_type="tool.error",
                session_id=session_id,
                tool_name=tool_name,
                risk_level=risk.value,
                decision="allow",
                details={"error": str(e), "duration_ms": duration_ms},
            )
            return ToolResult(
                tool_call_id=tool_call_id,
                name=tool_name,
                success=False,
                error=f"Runtime error executing tool '{tool_name}': {e}",
                duration_ms=duration_ms,
            )
