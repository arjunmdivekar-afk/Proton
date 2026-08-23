"""Unit tests for Proton Autonomous Voice Mode (STT, TTS, Wake Word, Commands, and Streaming)."""

import pytest
from proton.voice.wakeword import WakeWordDetector
from proton.voice.commands import VoiceCommandDispatcher
from proton.voice.tts import TextToSpeechEngine, TTSConfig, SentenceStreamBuffer
from proton.voice.stt import SpeechToTextEngine, STTConfig
from proton.core.config import ConfigManager


def test_wake_word_detection():
    """Test wake word matcher and prefix stripping."""
    detector = WakeWordDetector(enabled=True)

    # Positive matches
    assert detector.contains_wake_word("Hey Proton, can you help me?")
    assert detector.contains_wake_word("proton what is the current status")
    assert detector.contains_wake_word("OK Proton write a script")

    # Negative matches
    assert not detector.contains_wake_word("hello computer")
    assert not detector.contains_wake_word("python is cool")

    # Command extraction
    extracted = detector.extract_command("Hey Proton, read the readme file")
    assert extracted == "read the readme file"

    extracted2 = detector.extract_command("Proton: check git status")
    assert extracted2 == "check git status"


def test_voice_command_dispatcher(tmp_path, monkeypatch):
    """Test voice command pattern matching and execution."""
    monkeypatch.setenv("PROTON_HOME", str(tmp_path / ".proton"))
    config_mgr = ConfigManager()
    dispatcher = VoiceCommandDispatcher(config_manager=config_mgr)

    # 1. Stop / Interruption
    res_stop = dispatcher.dispatch("stop")
    assert res_stop.is_command is True
    assert res_stop.should_interrupt is True
    assert res_stop.command_name == "stop"

    res_quiet = dispatcher.dispatch("be quiet")
    assert res_quiet.is_command is True
    assert res_quiet.should_interrupt is True

    # 2. Exit Voice Mode
    res_exit = dispatcher.dispatch("exit voice")
    assert res_exit.is_command is True
    assert res_exit.should_exit is True
    assert res_exit.command_name == "exit"

    # 3. Status check
    res_status = dispatcher.dispatch("status")
    assert res_status.is_command is True
    assert "Proton is online" in res_status.feedback_speech

    # 4. Switch Model
    res_model = dispatcher.dispatch("switch model to llama-3.2-3b")
    assert res_model.is_command is True
    assert res_model.command_name == "switch_model"
    assert config_mgr.config.active_model == "llama-3.2-3b"

    # 5. Clear history
    res_clear = dispatcher.dispatch("clear history")
    assert res_clear.is_command is True
    assert res_clear.action_data.get("action") == "reset_session"

    # 6. Non-command natural question
    res_regular = dispatcher.dispatch("How does GraphRAG build the AST knowledge graph?")
    assert res_regular.is_command is False


def test_sentence_stream_buffer():
    """Test sentence boundary detection and real-time chunking for TTS."""
    sentences = []

    def on_sentence(s: str):
        sentences.append(s)

    buffer = SentenceStreamBuffer(on_sentence_ready=on_sentence)

    # Stream tokens one by one
    tokens = ["Hello", " world", "! ", "This", " is", " Proton", " speaking", ". ", "How", " can", " I", " help", "?"]
    for t in tokens:
        buffer.add_token(t)

    buffer.flush()

    assert len(sentences) == 3
    assert sentences[0] == "Hello world!"
    assert sentences[1] == "This is Proton speaking."
    assert sentences[2] == "How can I help?"


def test_tts_markdown_cleaning():
    """Test that TTS strips markdown syntax, code blocks, and links."""
    raw = "# Welcome to Proton!\n\nHere is a `var_name` and a [link](http://test.com).\n```python\nprint(1)\n```\nAll done."
    clean = TextToSpeechEngine._clean_markdown(raw)

    assert "Welcome to Proton!" in clean
    assert "var_name" in clean
    assert "link" in clean
    assert "http://test.com" not in clean
    assert "#" not in clean
    assert "`" not in clean
    assert "[Code block omitted]" in clean


def test_stt_engine_graceful_fallback():
    """Test that STT engine initializes cleanly even without physical microphone."""
    cfg = STTConfig()
    engine = SpeechToTextEngine(cfg)
    # Should not raise exception
    engine.calibrate_noise(duration=0.1)
    res = engine.transcribe_audio_file("non_existent.wav")
    assert res is None
