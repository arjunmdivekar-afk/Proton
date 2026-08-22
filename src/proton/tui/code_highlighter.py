"""Stream-aware code block and markdown syntax highlighter for Proton REPL."""

import re
from rich.console import Console
from rich.markup import escape


class StreamingCodeHighlighter:
    """Stream-aware formatter that highlights code blocks with a light-grey background."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.in_code_block = False
        self.code_lang = ""
        self.buffer = ""

    def process_chunk(self, chunk: str) -> None:
        self.buffer += chunk

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self._render_line(line)

    def _render_line(self, line: str) -> None:
        stripped = line.strip()

        # Check for triple-backtick code block start/end
        if stripped.startswith("```"):
            if not self.in_code_block:
                # Entering code block
                self.in_code_block = True
                self.code_lang = stripped[3:].strip()
                lang_label = f" {self.code_lang.upper()} " if self.code_lang else " CODE "
                self.console.print(f"[dim]--[/dim] [bold cyan on grey23]{lang_label}[/bold cyan on grey23] [dim]----------------------------------------------[/dim]")
            else:
                # Exiting code block
                self.in_code_block = False
                self.code_lang = ""
                self.console.print("[dim]----------------------------------------------------------[/dim]")
        elif self.in_code_block:
            # Code block line: highlight with subtle light grey background and clean white text
            escaped_code = escape(line)
            self.console.print(f"  [bright_white on grey15]{escaped_code}[/bright_white on grey15]", highlight=False)
        else:
            # Normal conversational text line (with inline `code` highlighting if present)
            self._render_regular_line(line)
            self.console.print()

    def _render_regular_line(self, line: str) -> None:
        if "`" in line:
            parts = re.split(r"(`[^`]+`)", line)
            styled = []
            for part in parts:
                if part.startswith("`") and part.endswith("`") and len(part) >= 2:
                    content = escape(part[1:-1])
                    styled.append(f"[bold cyan on grey23] {content} [/bold cyan on grey23]")
                else:
                    styled.append(escape(part))
            self.console.print("".join(styled), highlight=False, end="")
        else:
            self.console.print(escape(line), highlight=False, end="")

    def flush(self) -> None:
        if self.buffer:
            if self.in_code_block:
                escaped_code = escape(self.buffer)
                self.console.print(f"  [bright_white on grey15]{escaped_code}[/bright_white on grey15]", highlight=False)
            else:
                self._render_regular_line(self.buffer)
                self.console.print()
            self.buffer = ""
