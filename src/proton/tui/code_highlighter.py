"""Stream-aware code block, heading, and markdown syntax highlighter for Proton."""

import re
import sys
from rich.console import Console
from rich.markup import escape

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class StreamingCodeHighlighter:
    """Stream-aware formatter that highlights code blocks, resizes headings (#), and highlights markdown text (*)."""

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
                self.console.print(f"\n[dim]--[/dim] [bold cyan on grey23]{lang_label}[/bold cyan on grey23] [dim]----------------------------------------------[/dim]")
            else:
                # Exiting code block
                self.in_code_block = False
                self.code_lang = ""
                self.console.print("[dim]----------------------------------------------------------[/dim]\n")
        elif self.in_code_block:
            # Code block line: highlight with subtle light grey background and clean white text
            escaped_code = escape(line)
            self.console.print(f"  [bright_white on grey15]{escaped_code}[/bright_white on grey15]", highlight=False)
        else:
            # Markdown Headings (#) -> Change Size and Visual Prominence
            if stripped.startswith("#"):
                m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
                if m:
                    level = len(m.group(1))
                    heading_text = escape(m.group(2).strip())
                    if level == 1:
                        divider = "=" * min(65, max(30, len(heading_text) + 8))
                        self.console.print(f"\n[bold bright_white on grey23]  # {heading_text.upper()}  [/bold bright_white on grey23]\n[dim]{divider}[/dim]")
                    elif level == 2:
                        divider = "-" * min(55, max(25, len(heading_text) + 6))
                        self.console.print(f"\n[bold cyan]## {heading_text}[/bold cyan]\n[dim]{divider}[/dim]")
                    elif level == 3:
                        self.console.print(f"\n[bold yellow]### {heading_text}[/bold yellow]")
                    else:
                        self.console.print(f"\n[bold cyan]#### {heading_text}[/bold cyan]")
                    return

            # Bullet list items (* item or - item)
            bullet_match = re.match(r"^(\s*)[*\-]\s+(.*)$", line)
            if bullet_match:
                indent = bullet_match.group(1)
                item_text = bullet_match.group(2)
                formatted = self._format_inline_markdown(item_text)
                self.console.print(f"{indent}[bold cyan]*[/bold cyan] {formatted}", highlight=False)
                return

            # Regular conversational text line (with inline `code` and *text* / **text** highlighting)
            formatted_line = self._format_inline_markdown(line)
            self.console.print(formatted_line, highlight=False)

    def _format_inline_markdown(self, text: str) -> str:
        """Format inline markdown elements: **highlight**, *highlight*, and `code`."""
        code_placeholders = []

        def code_sub(match):
            code_placeholders.append(match.group(1))
            return f"__CODE_PH_{len(code_placeholders)-1}__"

        temp = re.sub(r"(`[^`]+`)", code_sub, text)

        # Highlight double asterisks **text** with bright yellow on dark grey background
        temp = re.sub(r"\*\*([^*]+)\*\*", r"[bold bright_yellow on grey23] \1 [/bold bright_yellow on grey23]", temp)

        # Highlight single asterisk *text* with bold yellow accent
        temp = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"[bold yellow]\1[/bold yellow]", temp)

        # Escape non-markup characters
        escaped_temp = escape(temp)
        escaped_temp = escaped_temp.replace("&amp;", "&")
        escaped_temp = escaped_temp.replace("\\[bold bright_yellow on grey23\\]", "[bold bright_yellow on grey23]").replace("\\[/bold bright_yellow on grey23\\]", "[/bold bright_yellow on grey23]")
        escaped_temp = escaped_temp.replace("\\[bold yellow\\]", "[bold yellow]").replace("\\[/bold yellow\\]", "[/bold yellow]")
        escaped_temp = escaped_temp.replace("\\[bold cyan\\]", "[bold cyan]").replace("\\[/bold cyan\\]", "[/bold cyan]")

        # Restore code placeholders with light-grey background styling
        for i, code_val in enumerate(code_placeholders):
            inner_code = escape(code_val[1:-1])
            escaped_temp = escaped_temp.replace(f"__CODE_PH_{i}__", f"[bold cyan on grey23] {inner_code} [/bold cyan on grey23]")

        return escaped_temp

    def flush(self) -> None:
        if self.buffer:
            if self.in_code_block:
                escaped_code = escape(self.buffer)
                self.console.print(f"  [bright_white on grey15]{escaped_code}[/bright_white on grey15]", highlight=False)
            else:
                formatted = self._format_inline_markdown(self.buffer)
                self.console.print(formatted, highlight=False)
            self.buffer = ""
