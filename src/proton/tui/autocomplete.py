"""Slash command autocomplete for prompt_toolkit."""

from typing import Iterable
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

SLASH_COMMANDS = {
    "/inspect": "Deep repo inspection (/inspect [security|architecture|dependencies|tests|performance])",
    "/task": "Manage persistent tasks (/task create|list|show|run|pause|resume|cancel)",
    "/agent": "Launch Proton Max-Level Autonomous Agent (/agent <goal>)",
    "/stock": "Launch live stock tracker in Rupees (₹) (/stock [SYMBOL])",
    "/stocks": "Alias for /stock market dashboard",
    "/browser": "Launch Proton Browser with search and link navigation (/browser [--ai_mode])",
    "/web-search": "Search the web via DuckDuckGo and summarize with AI",
    "/search": "Quick DuckDuckGo web search",
    "/help": "Show available commands and usage guide",
    "/connection": "Open interactive connection manager (LM Studio / Ollama)",
    "/model": "List or switch active model",
    "/mode": "Switch mode (/mode chat or /mode agent)",
    "/new": "Start a fresh conversation session",
    "/rag": "Manage RAG index and search project docs",
    "/memory": "Search or add project rules and facts",
    "/review": "Review git diff or code changes",
    "/plan": "Generate step-by-step implementation plan",
    "/diff": "View unstaged git diff",
    "/status": "Show git repository and session status",
    "/clear": "Clear the terminal screen",
    "/doctor": "Run environment and connectivity diagnostics",
    "/export": "Export current session to markdown",
    "/exit": "Exit Proton session",
}


class SlashCommandCompleter(Completer):
    """Provides inline autocompletion for slash commands."""

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text_before_cursor = document.text_before_cursor
        if text_before_cursor.startswith("/"):
            word = text_before_cursor.strip()
            for cmd, desc in SLASH_COMMANDS.items():
                if cmd.startswith(word):
                    yield Completion(
                        cmd,
                        start_position=-len(word),
                        display=f"{cmd:<14} {desc}",
                        display_meta=desc,
                    )
