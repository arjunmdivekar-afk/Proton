"""CLI command for Proton Max-Level Autonomous Agent (`proton agent`)."""

import asyncio
from typing import Optional
import typer

from proton.agent.max_agent import ProtonMaxAgent


def launch_max_agent(
    goal: Optional[str] = typer.Argument(
        None,
        help="Goal or task description for the autonomous agent to plan and execute.",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        "-y",
        help="Bypass plan and tool approval prompts for autonomous unattended execution.",
    ),
    max_steps: int = typer.Option(
        25,
        "--max-steps",
        "-s",
        help="Maximum agent turn steps before termination.",
    ),
) -> None:
    """Launch Proton Max-Level Autonomous Agent — 10-stage lifecycle with planning, tools, test verification, self-healing, and audit reporting."""
    if not goal:
        goal = typer.prompt("Enter task goal for Proton Agent")

    agent = ProtonMaxAgent(auto_approve=auto_approve, max_steps=max_steps)
    asyncio.run(agent.run(goal))
