"""VoiceModeEngine - Orchestrates Speech I/O, LLM Inference, and Commands."""

import asyncio
import time
import sys
import logging
from typing import Optional, List
from pydantic import BaseModel
from rich.console import Console
from rich.live import Live

from proton.voice.stt import SpeechToTextEngine, STTConfig
from proton.voice.tts import TextToSpeechEngine, TTSConfig, SentenceStreamBuffer
from proton.voice.wakeword import WakeWordDetector
from proton.voice.commands import VoiceCommandDispatcher, VoiceCommandResult
from proton.voice.tui import VoiceTUI
from proton.core.config import ConfigManager
from proton.connection.manager import ConnectionManager
from proton.providers.registry import ProviderRegistry
from proton.core.types import Message, Role
from proton.agent.context import ContextAssembler

logger = logging.getLogger(__name__)


class VoiceModeConfig(BaseModel):
    """Configuration for Proton Voice Mode session."""
    wake_word_mode: bool = False  # If True, requires 'Hey Proton' before speaking
    stt_config: STTConfig = STTConfig()
    tts_config: TTSConfig = TTSConfig()
    system_prompt: str = "You are Proton, an AI assistant. Keep voice answers concise, direct, and conversational."


class VoiceModeEngine:
    """Main controller running the live autonomous voice loop."""

    def __init__(
        self,
        config: Optional[VoiceModeConfig] = None,
        config_manager: Optional[ConfigManager] = None,
        console: Optional[Console] = None,
    ):
        self.config = config or VoiceModeConfig()
        self.config_mgr = config_manager or ConfigManager()
        self.conn_mgr = ConnectionManager(self.config_mgr)
        self.console = console or Console()

        self.stt = SpeechToTextEngine(self.config.stt_config)
        self.tts = TextToSpeechEngine(self.config.tts_config)
        self.wakeword = WakeWordDetector(enabled=self.config.wake_word_mode)
        self.commands = VoiceCommandDispatcher(self.config_mgr)
        self.tui = VoiceTUI(self.console)

        self.messages: List[Message] = [
            Message(role=Role.SYSTEM, content=self.config.system_prompt)
        ]
        self._running = False

    async def run_async(self) -> None:
        """Run the interactive voice loop with Rich live rendering."""
        self._running = True
        self.stt.calibrate_noise(duration=0.8)

        active_conn = self.conn_mgr.get_active_connection()
        self.tui.active_provider = active_conn.name if active_conn else "proton-hub"
        self.tui.active_model = self.config_mgr.config.active_model or "default"

        # Welcome announcement
        welcome_msg = "Proton Voice Mode online. How can I help you?"
        self.tui.last_assistant_speech = welcome_msg
        self.tts.speak(welcome_msg)

        with Live(self.tui.render_panel(), console=self.console, refresh_per_second=10) as live:
            while self._running:
                # Update current provider & model
                active_conn = self.conn_mgr.get_active_connection()
                self.tui.active_provider = active_conn.name if active_conn else "proton-hub"
                self.tui.active_model = self.config_mgr.config.active_model or "default"

                # 1. Listening State
                if self.config.wake_word_mode:
                    self.tui.state = "WAKING"
                else:
                    self.tui.state = "LISTENING"
                live.update(self.tui.render_panel())

                # Transcribe speech (runs in executor to avoid blocking asyncio event loop)
                loop = asyncio.get_running_loop()
                spoken_text = await loop.run_in_executor(None, self.stt.listen_and_transcribe)

                if not spoken_text:
                    await asyncio.sleep(0.1)
                    live.update(self.tui.render_panel())
                    continue

                # 2. Check Wake Word
                if self.config.wake_word_mode:
                    if not self.wakeword.contains_wake_word(spoken_text):
                        continue
                    spoken_text = self.wakeword.extract_command(spoken_text)
                    if not spoken_text:
                        self.tts.speak("Yes, I'm listening.")
                        continue

                self.tui.last_user_speech = spoken_text
                live.update(self.tui.render_panel())

                # 3. Check Voice Commands (stop, exit, switch model, etc.)
                cmd_res = self.commands.dispatch(spoken_text)
                if cmd_res.is_command:
                    self.tui.state = "COMMAND"
                    live.update(self.tui.render_panel())

                    if cmd_res.should_interrupt:
                        self.tts.interrupt()

                    if cmd_res.feedback_speech:
                        self.tui.last_assistant_speech = cmd_res.feedback_speech
                        self.tts.speak(cmd_res.feedback_speech)

                    if cmd_res.action_data.get("action") == "reset_session":
                        self.messages = [Message(role=Role.SYSTEM, content=self.config.system_prompt)]

                    if cmd_res.should_exit:
                        # Wait for goodbye to finish speaking
                        while self.tts.is_speaking:
                            await asyncio.sleep(0.1)
                        self._running = False
                        break

                    continue

                # 4. LLM Streaming Response & Sentence TTS
                self.tui.state = "THINKING"
                live.update(self.tui.render_panel())

                await self._process_conversation(spoken_text, live)

        self.tts.shutdown()

    async def _process_conversation(self, user_prompt: str, live: Live) -> None:
        """Stream LLM response and dispatch completed sentences to TTS."""
        self.messages.append(Message(role=Role.USER, content=user_prompt))

        active_conn = self.conn_mgr.get_active_connection()
        if not active_conn:
            err_msg = "No active connection configured."
            self.tui.last_assistant_speech = err_msg
            self.tts.speak(err_msg)
            return

        provider = ProviderRegistry.get_provider_for_connection(active_conn)
        model_id = self.config_mgr.config.active_model or "default"

        assistant_full_text = ""
        token_count = 0
        t_start = time.perf_counter()

        def on_sentence(sentence: str):
            self.tui.state = "SPEAKING"
            self.tts.speak(sentence)

        stream_buffer = SentenceStreamBuffer(on_sentence_ready=on_sentence)

        try:
            async for chunk in provider.stream_chat(
                messages=self.messages,
                model=model_id,
                temperature=0.7,
                max_tokens=512,
            ):
                if hasattr(chunk, "delta"):
                    delta = chunk.delta or ""
                elif hasattr(chunk, "text"):
                    delta = chunk.text or ""
                elif isinstance(chunk, str):
                    delta = chunk
                else:
                    delta = getattr(chunk, "content", "")

                if delta:
                    token_count += 1
                    assistant_full_text += delta
                    self.tui.last_assistant_speech = assistant_full_text

                    elapsed = time.perf_counter() - t_start
                    self.tui.tok_speed = token_count / elapsed if elapsed > 0 else 0.0
                    self.tui.latency_ms = elapsed * 1000

                    stream_buffer.add_token(delta)
                    live.update(self.tui.render_panel())

            # Flush any remaining text to TTS
            stream_buffer.flush()
            self.messages.append(Message(role=Role.ASSISTANT, content=assistant_full_text))

            # Wait while audio finishes playing
            while self.tts.is_speaking and self._running:
                self.tui.state = "SPEAKING"
                live.update(self.tui.render_panel())
                await asyncio.sleep(0.05)

            # Immediately restore listening state for continuous turn
            if self.config.wake_word_mode:
                self.tui.state = "WAKING"
            else:
                self.tui.state = "LISTENING"
            live.update(self.tui.render_panel())

        except Exception as e:
            err_msg = f"Inference error: {str(e)}"
            self.tui.last_assistant_speech = err_msg
            self.tts.speak("I encountered an error generating the response.")
            logger.error(f"Voice generation failed: {e}")

    def run_sync(self) -> None:
        """Synchronous entrypoint to run voice mode."""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            self.console.print("\n[dim]Proton Voice Mode terminated by user.[/dim]")
            self.tts.shutdown()
