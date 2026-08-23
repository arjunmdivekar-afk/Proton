"""Rich Terminal TUI Audio HUD for Proton Voice Mode."""

import time
import math
from typing import Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.layout import Layout


class VoiceTUI:
    """Renders real-time audio visualization, waveform, and state HUD in the terminal."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.state = "INITIALIZING"  # 'LISTENING', 'THINKING', 'SPEAKING', 'WAKING', 'IDLE'
        self.active_provider = "proton-hub"
        self.active_model = "Llama-3.2-1B-Instruct"
        self.last_user_speech = ""
        self.last_assistant_speech = ""
        self.tok_speed = 0.0
        self.latency_ms = 0.0
        self._wave_tick = 0

    def generate_waveform(self, active: bool = False) -> str:
        """Generate animated text-based audio waveform."""
        bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        out = []
        for i in range(24):
            if active:
                val = int(4 + 3.5 * math.sin((self._wave_tick + i) * 0.45))
                out.append(bars[min(max(val, 0), len(bars) - 1)])
            else:
                out.append("─")
        return "".join(out)

    def render_panel(self) -> Panel:
        """Construct the Rich visual HUD panel."""
        self._wave_tick += 1

        # Status badge & color
        status_map = {
            "LISTENING": ("🎙️  LISTENING (Speak now)", "bold green"),
            "THINKING": ("🧠  THINKING...", "bold cyan"),
            "SPEAKING": ("🔊  SPEAKING...", "bold magenta"),
            "WAKING": ("👂  AWAITING WAKE WORD ('Hey Proton')", "bold yellow"),
            "IDLE": ("💤  IDLE", "dim white"),
            "COMMAND": ("⚡  EXECUTING COMMAND", "bold bright_yellow"),
        }

        status_label, status_style = status_map.get(self.state, ("🎙️  VOICE ACTIVE", "bold white"))
        is_active_audio = self.state in ("LISTENING", "SPEAKING")
        waveform_str = self.generate_waveform(is_active_audio)

        header_table = Table.grid(expand=True)
        header_table.add_column(ratio=1)
        header_table.add_column(justify="right")

        header_table.add_row(
            Text.from_markup(f"[{status_style}]{status_label}[/{status_style}]"),
            Text(f"Provider: {self.active_provider} • Model: {self.active_model}", style="dim"),
        )

        content_elements = [
            header_table,
            Text.from_markup(f"\n[cyan]Audio Waveform:[/cyan] [bold bright_cyan]{waveform_str}[/bold bright_cyan]\n"),
        ]

        if self.last_user_speech:
            content_elements.append(Text.from_markup(f"[bold white]You:[/bold white] {self.last_user_speech}"))

        if self.last_assistant_speech:
            content_elements.append(Text.from_markup(f"[bold magenta]Proton:[/bold magenta] {self.last_assistant_speech}"))

        if self.tok_speed > 0 or self.latency_ms > 0:
            content_elements.append(Text(f"\n⚡ Speed: {self.tok_speed:.1f} tok/s  •  Latency: {self.latency_ms:.0f} ms", style="dim italic"))

        content_elements.append(Text("\n(Say 'stop' to interrupt, 'exit' to quit voice mode, or press Ctrl+C)", style="dim"))

        return Panel(
            Group(*content_elements),
            title="[bold cyan]⚛️ PROTON AUTONOMOUS VOICE MODE v2.6.4[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
