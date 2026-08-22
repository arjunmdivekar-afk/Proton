"""Human-in-the-loop approval manager for Proton."""

import asyncio
from typing import Callable, Dict, Optional, Set
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from proton.core.types import RiskLevel, ApprovalDecision, ApprovalPolicy
from proton.core.events import event_bus, Event, EventType
from proton.core.exceptions import ApprovalDeniedError


ApprovalCallback = Callable[[str, dict, RiskLevel], ApprovalDecision]


class ApprovalManager:
    """Handles interactive or automated policy-based user approvals."""

    def __init__(self, policy: ApprovalPolicy = ApprovalPolicy.STRICT) -> None:
        self.policy = policy
        self._session_allowed_tools: Set[str] = set()
        self._custom_handler: Optional[ApprovalCallback] = None

    def set_custom_handler(self, handler: ApprovalCallback) -> None:
        self._custom_handler = handler

    async def request_approval(self, tool_name: str, arguments: dict, risk_level: RiskLevel) -> bool:
        """Prompt user or evaluate session allowances before tool execution."""
        # Check if already approved for session
        if tool_name in self._session_allowed_tools:
            return True

        # Policy checks
        if self.policy == ApprovalPolicy.AUTONOMOUS and risk_level != RiskLevel.DESTRUCTIVE:
            return True

        if self.policy == ApprovalPolicy.BALANCED and risk_level == RiskLevel.SAFE:
            return True

        # Strict or elevated risk requires approval
        await event_bus.emit(
            Event(
                type=EventType.APPROVAL_REQUESTED,
                data={"tool": tool_name, "arguments": arguments, "risk": risk_level.value},
            )
        )

        decision: ApprovalDecision
        if self._custom_handler:
            decision = self._custom_handler(tool_name, arguments, risk_level)
        else:
            decision = await self._prompt_terminal(tool_name, arguments, risk_level)

        await event_bus.emit(
            Event(
                type=EventType.APPROVAL_RESOLVED,
                data={"tool": tool_name, "decision": decision.value},
            )
        )

        if decision == ApprovalDecision.ALLOW_SESSION:
            self._session_allowed_tools.add(tool_name)
            return True
        elif decision == ApprovalDecision.ALLOW_ONCE:
            return True
        else:
            raise ApprovalDeniedError(f"User denied execution of tool '{tool_name}'.")

    async def _prompt_terminal(self, tool_name: str, arguments: dict, risk_level: RiskLevel) -> ApprovalDecision:
        """Show Rich prompt in terminal."""
        console = Console()
        color = "yellow" if risk_level in (RiskLevel.SAFE, RiskLevel.MODIFICATION) else "red"
        
        args_str = "\n".join(f"  {k}: {str(v)[:150]}" for k, v in arguments.items())
        panel = Panel(
            f"[bold {color}]APPROVAL REQUIRED FOR TOOL EXECUTION[/bold {color}]\n\n"
            f"[bold]Tool:[/bold] [cyan]{tool_name}[/cyan]\n"
            f"[bold]Risk Level:[/bold] [{color}]{risk_level.value.upper()}[/{color}]\n"
            f"[bold]Arguments:[/bold]\n{args_str}",
            border_style=color,
        )
        console.print(panel)
        console.print("[bold]1. Allow Once[/bold]  [bold]2. Allow for Session[/bold]  [bold]3. Deny[/bold]")
        
        # Run prompt in executor to not block async loop
        loop = asyncio.get_running_loop()
        choice = await loop.run_in_executor(
            None,
            lambda: Prompt.ask("Your decision", choices=["1", "2", "3"], default="1")
        )

        if choice == "1":
            return ApprovalDecision.ALLOW_ONCE
        elif choice == "2":
            return ApprovalDecision.ALLOW_SESSION
        else:
            return ApprovalDecision.DENY
