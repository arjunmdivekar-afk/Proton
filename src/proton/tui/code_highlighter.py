"""Stream-aware code block, large heading (#), and markdown syntax highlighter for Proton."""

import re
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class StreamingCodeHighlighter:
    """Stream-aware formatter that highlights code blocks, renders large prominent headings (#), and highlights markdown text (*)."""

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
            code_text = Text("  ")
            code_text.append(line, style="bright_white on grey15")
            self.console.print(code_text)
        else:
            # Markdown Headings (#) -> Render with Large Visual Size and Prominent Framing
            if stripped.startswith("#"):
                heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
                if heading_match:
                    level = len(heading_match.group(1))
                    heading_text = heading_match.group(2).strip()

                    if level == 1:
                        # Level 1 (#): Large double-padded heading panel banner
                        p = Panel.fit(
                            f"\n[bold bright_white on grey23]  # {heading_text.upper()}  [/bold bright_white on grey23]\n",
                            border_style="bold cyan",
                            style="bold bright_white on grey23",
                        )
                        self.console.print()
                        self.console.print(p)
                        self.console.print()
                    elif level == 2:
                        # Level 2 (##): Framed section header
                        p = Panel.fit(
                            f"[bold cyan]## {heading_text}[/bold cyan]",
                            border_style="cyan",
                        )
                        self.console.print()
                        self.console.print(p)
                    elif level == 3:
                        # Level 3 (###): Subsection header with bright yellow accent
                        self.console.print(f"\n[bold bright_yellow]### {heading_text}[/bold bright_yellow]")
                    else:
                        self.console.print(f"\n[bold cyan]#### {heading_text}[/bold cyan]")
                    return

            # Bullet list items (* item or - item)
            bullet_match = re.match(r"^(\s*)[*\-]\s+(.*)$", line)
            if bullet_match:
                indent = bullet_match.group(1)
                item_text = bullet_match.group(2)
                t = Text(indent)
                t.append("* ", style="bold cyan")
                t.append_text(self._parse_inline_styles(item_text))
                self.console.print(t)
                return

            # Regular text line with inline formatting
            t = self._parse_inline_styles(line)
            self.console.print(t)

    def _parse_inline_styles(self, text: str) -> Text:
        """Parse inline **bold/highlight**, *italic*, and `code` into a native styled Rich Text object."""
        # Tokenize by inline code, double asterisks, and single asterisks
        pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*))")
        tokens = pattern.split(text)

        res = Text()
        for tok in tokens:
            if not tok:
                continue
            if tok.startswith("`") and tok.endswith("`") and len(tok) >= 2:
                # Inline code: light grey background with cyan text
                res.append(f" {tok[1:-1]} ", style="bold cyan on grey23")
            elif tok.startswith("**") and tok.endswith("**") and len(tok) >= 4:
                # **Highlighted text**: bright yellow bold highlight on dark background
                res.append(f" {tok[2:-2]} ", style="bold bright_yellow on grey23")
            elif tok.startswith("*") and tok.endswith("*") and len(tok) >= 2:
                # *Italic / highlighted text*: bold yellow
                res.append(tok[1:-1], style="bold yellow")
            else:
                res.append(tok)
        return res

    def flush(self) -> None:
        if self.buffer:
            if self.in_code_block:
                code_text = Text("  ")
                code_text.append(self.buffer, style="bright_white on grey15")
                self.console.print(code_text)
            else:
                t = self._parse_inline_styles(self.buffer)
                self.console.print(t)
            self.buffer = ""
