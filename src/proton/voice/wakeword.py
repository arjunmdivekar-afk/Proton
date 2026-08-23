"""Wake Word Detection Engine for Proton."""

import re
import logging
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Detects wake words in transcribed audio phrases."""

    DEFAULT_WAKE_WORDS = ["hey proton", "proton", "ok proton", "hello proton", "hi proton"]

    def __init__(self, wake_words: Optional[List[str]] = None, enabled: bool = True):
        self.enabled = enabled
        self.wake_words: List[str] = [w.lower().strip() for w in (wake_words or self.DEFAULT_WAKE_WORDS)]
        self._patterns = [
            re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in self.wake_words
        ]

    def contains_wake_word(self, text: str) -> bool:
        """Check if phrase contains configured wake word."""
        if not self.enabled:
            return True
        if not text or not text.strip():
            return False

        clean = text.lower().strip()
        return any(pattern.search(clean) for pattern in self._patterns)

    def extract_command(self, text: str) -> str:
        """Extract the actual user command trailing the wake word."""
        if not text:
            return ""

        clean = text.strip()
        if not self.enabled:
            return clean

        # Strip out matched wake word prefix
        for w in sorted(self.wake_words, key=len, reverse=True):
            pattern = re.compile(rf"^\s*{re.escape(w)}[,\s:]*", re.IGNORECASE)
            if pattern.search(clean):
                return pattern.sub("", clean).strip()

        return clean
