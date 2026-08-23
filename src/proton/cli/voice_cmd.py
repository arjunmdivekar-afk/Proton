"""CLI subcommand for launching Proton Voice Mode."""

import typer
from rich.console import Console
from typing import Optional

from proton.voice.engine import VoiceModeEngine, VoiceModeConfig
from proton.voice.stt import STTConfig
from proton.voice.tts import TTSConfig
from proton.core.config import ConfigManager

voice_app = typer.Typer(name="voice", help="Launch Proton Autonomous Voice Mode (STT & TTS)")
console = Console()


@voice_app.callback(invoke_without_command=True)
def run_voice(
    wake_word: bool = typer.Option(False, "--wake-word", "-w", help="Require 'Hey Proton' wake word to activate"),
    rate: int = typer.Option(190, "--rate", "-r", help="Text-to-Speech playback speed (words per minute)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override active AI model for voice session"),
) -> None:
    """Launch Proton real-time Voice Mode."""
    config_mgr = ConfigManager()
    if model:
        config_mgr.set_active_model(model)

    voice_cfg = VoiceModeConfig(
        wake_word_mode=wake_word,
        tts_config=TTSConfig(rate=rate),
    )

    engine = VoiceModeEngine(config=voice_cfg, config_manager=config_mgr, console=console)
    engine.run_sync()
