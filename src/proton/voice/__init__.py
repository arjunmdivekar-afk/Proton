"""Proton Autonomous Voice Mode package.

Provides Speech-to-Text (STT), Text-to-Speech (TTS), Wake Word Detection,
Voice Commands, Streaming Audio Synthesis, and Terminal Audio HUD.
"""

from proton.voice.engine import VoiceModeEngine, VoiceModeConfig
from proton.voice.stt import SpeechToTextEngine
from proton.voice.tts import TextToSpeechEngine
from proton.voice.wakeword import WakeWordDetector
from proton.voice.commands import VoiceCommandDispatcher, VoiceCommandResult
from proton.voice.tui import VoiceTUI

__all__ = [
    "VoiceModeEngine",
    "VoiceModeConfig",
    "SpeechToTextEngine",
    "TextToSpeechEngine",
    "WakeWordDetector",
    "VoiceCommandDispatcher",
    "VoiceCommandResult",
    "VoiceTUI",
]
