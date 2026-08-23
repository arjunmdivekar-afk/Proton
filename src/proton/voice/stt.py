"""Speech-to-Text (STT) Engine with Local Whisper and SoundDevice VAD."""

import os
import sys
import time
import queue
import logging
from typing import Optional, Callable, List
from pydantic import BaseModel
import numpy as np

logger = logging.getLogger(__name__)


class STTConfig(BaseModel):
    """Configuration for Speech-to-Text capture and transcription."""
    engine: str = "whisper"  # 'whisper', 'speech_recognition', 'auto'
    model_size: str = "tiny.en"  # 'tiny.en', 'base.en', 'small.en'
    energy_threshold: float = 0.015  # RMS energy threshold for sounddevice VAD
    silence_duration: float = 1.0  # Seconds of silence to trigger end of utterance
    sample_rate: int = 16000
    language: str = "en"


class SpeechToTextEngine:
    """High-performance local Speech-to-Text engine using Whisper and SoundDevice."""

    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self._whisper_model = None
        self._sd_available = False
        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize local Whisper model and sounddevice capture."""
        # 1. Check sounddevice
        try:
            import sounddevice as sd
            self._sd_available = True
        except ImportError:
            self._sd_available = False

        # 2. Check local Whisper model
        try:
            from faster_whisper import WhisperModel
            # Load quantized local model for maximum CPU/GPU efficiency
            self._whisper_model = WhisperModel(
                self.config.model_size,
                device="cpu",
                compute_type="int8",
                download_root=os.path.join(os.path.expanduser("~"), ".proton", "models", "whisper"),
            )
            logger.info(f"Loaded local Whisper STT model ({self.config.model_size})")
        except Exception as e:
            logger.info(f"Local faster-whisper not active ({e}). Using SpeechRecognition fallback.")
            self._whisper_model = None

    def calibrate_noise(self, duration: float = 0.5) -> None:
        """Calibrate microphone ambient background noise level using sounddevice."""
        if not self._sd_available:
            return

        try:
            import sounddevice as sd
            samples = int(self.config.sample_rate * duration)
            rec = sd.rec(samples, samplerate=self.config.sample_rate, channels=1, dtype="float32")
            sd.wait()
            rms = float(np.sqrt(np.mean(rec**2)))
            # Set dynamic threshold slightly above ambient noise
            self.config.energy_threshold = max(0.012, rms * 1.5)
        except Exception as e:
            logger.debug(f"SoundDevice noise calibration bypassed: {e}")

    def listen_and_transcribe(
        self,
        timeout: Optional[float] = 12.0,
        phrase_time_limit: Optional[float] = 20.0,
        on_listening_start: Optional[Callable[[], None]] = None,
    ) -> Optional[str]:
        """Listen to microphone input with VAD and return transcribed text."""
        if on_listening_start:
            on_listening_start()

        # Primary: Local SoundDevice + Local Whisper Model
        if self._sd_available and self._whisper_model:
            audio_data = self._record_voice_activity(timeout=timeout, max_time=phrase_time_limit)
            if audio_data is not None and len(audio_data) > int(self.config.sample_rate * 0.4):
                return self._transcribe_whisper_array(audio_data)
            return None

        # Fallback 1: SpeechRecognition library
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.pause_threshold = 1.0
            with sr.Microphone(sample_rate=self.config.sample_rate) as source:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return recognizer.recognize_google(audio).strip()
        except Exception:
            pass

        # Fallback 2: Interactive Terminal Input
        try:
            text = input("\n🎙️  [Speak / Type]: ").strip()
            return text if text else None
        except (EOFError, KeyboardInterrupt):
            return "exit"

    def _record_voice_activity(
        self,
        timeout: Optional[float] = 12.0,
        max_time: Optional[float] = 20.0,
    ) -> Optional[np.ndarray]:
        """Record audio stream until speech completes with VAD silence detection."""
        import sounddevice as sd

        chunk_duration = 0.05  # 50ms chunks
        chunk_size = int(self.config.sample_rate * chunk_duration)
        q: queue.Queue = queue.Queue()

        def audio_callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Audio status: {status}")
            q.put(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_size,
                callback=audio_callback,
            ):
                recorded_frames: List[np.ndarray] = []
                speech_started = False
                silence_start_time = None
                start_time = time.perf_counter()

                while True:
                    elapsed = time.perf_counter() - start_time
                    if not speech_started and timeout and elapsed > timeout:
                        return None
                    if max_time and elapsed > max_time:
                        break

                    try:
                        chunk = q.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    recorded_frames.append(chunk)
                    rms = float(np.sqrt(np.mean(chunk**2)))

                    if rms > self.config.energy_threshold:
                        speech_started = True
                        silence_start_time = None
                    elif speech_started:
                        if silence_start_time is None:
                            silence_start_time = time.perf_counter()
                        elif time.perf_counter() - silence_start_time > self.config.silence_duration:
                            # User finished speaking
                            break

                if not speech_started or not recorded_frames:
                    return None

                full_audio = np.concatenate(recorded_frames, axis=0).flatten()
                return full_audio
        except Exception as e:
            logger.debug(f"SoundDevice record error: {e}")
            return None

    def _transcribe_whisper_array(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe floating-point audio numpy array using local Whisper model."""
        if not self._whisper_model:
            return None

        try:
            segments, _ = self._whisper_model.transcribe(
                audio,
                beam_size=5,
                language=self.config.language,
                vad_filter=True,
            )
            text = " ".join([s.text for s in segments]).strip()
            return text if text else None
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return None

    def transcribe_audio_file(self, file_path: str) -> Optional[str]:
        """Transcribe an audio file on disk with local Whisper."""
        if not os.path.exists(file_path):
            return None

        if self._whisper_model:
            try:
                segments, _ = self._whisper_model.transcribe(file_path, beam_size=5)
                return " ".join([s.text for s in segments]).strip()
            except Exception as e:
                logger.debug(f"Whisper file transcription failed: {e}")

        return None
