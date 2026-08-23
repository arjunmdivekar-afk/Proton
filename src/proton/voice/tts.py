"""Text-to-Speech (TTS) Engine with Streaming Sentence Synthesis and Instant Interruption."""

import os
import re
import sys
import time
import queue
import threading
import logging
from typing import Optional, Callable, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TTSConfig(BaseModel):
    """Configuration for Text-to-Speech audio synthesis."""
    rate: int = 2  # -10 to +10 for SAPI (or 190 wpm)
    volume: int = 100  # 0 to 100
    voice_id: Optional[str] = None
    engine: str = "auto"


class TextToSpeechEngine:
    """Non-blocking streaming TTS synthesizer with sentence-level pipeline."""

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._speech_queue: queue.Queue = queue.Queue()
        self._is_speaking = False
        self._interrupted = threading.Event()
        self._shutdown = threading.Event()

        # Background worker thread for speech playback
        self._worker_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._worker_thread.start()

    def _playback_loop(self) -> None:
        """Background thread executing speech items sequentially from the queue."""
        speaker = None
        is_windows = sys.platform == "win32"

        # Initialize COM on the background thread on Windows
        if is_windows:
            try:
                import pythoncom
                import win32com.client
                pythoncom.CoInitialize()
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                # Set rate and volume
                try:
                    speaker.Rate = int(self.config.rate) if -10 <= self.config.rate <= 10 else 1
                    speaker.Volume = min(max(int(self.config.volume), 0), 100)
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"Failed to initialize SAPI.SpVoice: {e}")
                speaker = None

        while not self._shutdown.is_set():
            try:
                item = self._speech_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if item is None:
                break

            if self._interrupted.is_set():
                self._speech_queue.task_done()
                continue

            text, on_start, on_finish = item
            self._is_speaking = True
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass

            self._speak_text_internal(text, speaker)

            self._is_speaking = False
            if on_finish:
                try:
                    on_finish()
                except Exception:
                    pass
            self._speech_queue.task_done()

        if is_windows:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def _speak_text_internal(self, text: str, speaker) -> None:
        """Synthesize and play audio for a single sentence/paragraph."""
        if not text or not text.strip():
            return

        clean_text = self._clean_markdown(text)
        if not clean_text or self._interrupted.is_set():
            return

        # 1. Native Windows SAPI COM speaker (Thread-safe inside worker thread)
        if speaker and not self._interrupted.is_set():
            try:
                # SVSFlagsAsync = 1, SVSFPurgeBeforeSpeak = 2
                # We do synchronous speak inside the dedicated background worker thread
                speaker.Speak(clean_text, 0)
                return
            except Exception as e:
                logger.debug(f"SAPI speak error ({e})")

        # 2. Pyttsx3 fallback
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(clean_text)
            engine.runAndWait()
            return
        except Exception:
            pass

        # 3. PowerShell fallback
        if sys.platform == "win32" and not self._interrupted.is_set():
            try:
                import subprocess
                escaped = clean_text.replace('"', '""').replace("'", "''")
                cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{escaped}\')"'
                subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            except Exception as e:
                logger.debug(f"PowerShell speech fallback error: {e}")

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Strip markdown syntax, code blocks, URLs, and symbols for natural voice output."""
        # Replace code blocks with descriptive phrase
        t = re.sub(r'```[\s\S]*?```', ' [Code block omitted] ', text)
        # Inline code
        t = re.sub(r'`([^`]+)`', r'\1', t)
        # Markdown links: [text](url) -> text
        t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
        # Markdown headers
        t = re.sub(r'#{1,6}\s*', '', t)
        # Bold / italics with asterisks
        t = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', t)
        # Strikethrough
        t = re.sub(r'~~([^~]+)~~', r'\1', t)
        # Bullets and numbered lists
        t = re.sub(r'^\s*[-*+]\s+', '', t, flags=re.MULTILINE)
        t = re.sub(r'^\s*\d+\.\s+', '', t, flags=re.MULTILINE)
        # Excess whitespace
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def speak(
        self,
        text: str,
        on_start: Optional[Callable[[], None]] = None,
        on_finish: Optional[Callable[[], None]] = None,
    ) -> None:
        """Enqueue complete text for speech playback."""
        self._interrupted.clear()
        self._speech_queue.put((text, on_start, on_finish))

    def interrupt(self) -> None:
        """Immediately stop currently playing audio and clear remaining queue."""
        self._interrupted.set()
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except queue.Empty:
                break
        self._is_speaking = False

    @property
    def is_speaking(self) -> bool:
        """Check if speech audio is currently playing."""
        return self._is_speaking or not self._speech_queue.empty()

    def shutdown(self) -> None:
        """Gracefully stop TTS background thread."""
        self.interrupt()
        self._shutdown.set()
        self._speech_queue.put(None)
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)


class SentenceStreamBuffer:
    """Buffers streaming token deltas and extracts complete sentences for TTS synthesis."""

    SENTENCE_ENDINGS = re.compile(r'([.!?:\n]+(?:\s+|$))')

    def __init__(self, on_sentence_ready: Callable[[str], None]):
        self.on_sentence_ready = on_sentence_ready
        self.buffer = ""

    def add_token(self, delta: str) -> None:
        """Accumulate token delta and dispatch any completed sentences."""
        self.buffer += delta
        parts = self.SENTENCE_ENDINGS.split(self.buffer)

        # If we have complete sentences (pairs of sentence text + delimiter)
        if len(parts) > 2:
            sentence = "".join(parts[:2]).strip()
            self.buffer = "".join(parts[2:])
            if sentence:
                self.on_sentence_ready(sentence)

    def flush(self) -> None:
        """Flush remaining buffered text as the final sentence."""
        remaining = self.buffer.strip()
        if remaining:
            self.buffer = ""
            self.on_sentence_ready(remaining)
