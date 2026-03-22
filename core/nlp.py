"""
Natural Language Processing utilities for JARVIS.

Provides intent detection and basic entity extraction using NLTK.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional NLTK
# ---------------------------------------------------------------------------
try:
    import nltk  # type: ignore
    from nltk.tokenize import word_tokenize  # type: ignore
    from nltk.corpus import stopwords  # type: ignore

    _NLTK_AVAILABLE = True

    # Download required corpora silently on first use
    def _ensure_nltk_data():
        _resources = [
            ("tokenizers/punkt", "punkt"),
            ("corpora/stopwords", "stopwords"),
            ("tokenizers/punkt_tab", "punkt_tab"),
        ]
        for data_path, package in _resources:
            try:
                nltk.data.find(data_path)
            except LookupError:
                try:
                    nltk.download(package, quiet=True)
                except Exception:
                    pass

    _ensure_nltk_data()

except ImportError:
    _NLTK_AVAILABLE = False
    logger.warning("NLTK not installed – basic NLP only.")

# ---------------------------------------------------------------------------
# Intent patterns
# ---------------------------------------------------------------------------

# Each entry: (intent_name, [regex_patterns])
_INTENT_PATTERNS: List[Tuple[str, List[str]]] = [
    ("greeting", [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreet"]),
    ("farewell", [r"\bbye\b", r"\bgoodbye\b", r"\bexit\b", r"\bquit\b", r"\bsee you\b"]),
    ("thanks", [r"\bthank(s| you)\b", r"\bcheers\b"]),
    ("search", [r"\bsearch\b", r"\blook up\b", r"\bfind\b", r"\bgoogle\b"]),
    ("calculate", [r"\bcalculate\b", r"\bcompute\b", r"\bmath\b", r"\bsolve\b", r"\bwhat is \d"]),
    ("time", [r"\btime\b", r"\bclock\b", r"\bwhat time\b"]),
    ("date", [r"\bdate\b", r"\btoday\b", r"\bday\b", r"\bmonth\b", r"\byear\b"]),
    ("weather", [r"\bweather\b", r"\btemperature\b", r"\brain\b", r"\bsunny\b"]),
    ("joke", [r"\bjoke\b", r"\bfunny\b", r"\blaugh\b"]),
    ("open_app", [r"\bopen\b", r"\blaunch\b", r"\bstart\b"]),
    ("system_info", [r"\bsystem\b", r"\bcpu\b", r"\bmemory\b", r"\bram\b", r"\bdisk\b"]),
    ("help", [r"\bhelp\b", r"\bwhat can you do\b", r"\bcommands\b"]),
]


class NLPProcessor:
    """Lightweight intent detector and entity extractor."""

    def __init__(self):
        self._compiled = [
            (intent, [re.compile(p, re.IGNORECASE) for p in patterns])
            for intent, patterns in _INTENT_PATTERNS
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_intent(self, text: str) -> str:
        """
        Return the most likely intent name for *text*, or ``"unknown"``.
        """
        text_lower = text.lower()
        for intent, patterns in self._compiled:
            if any(p.search(text_lower) for p in patterns):
                return intent
        return "unknown"

    def extract_keywords(self, text: str) -> List[str]:
        """
        Return a list of meaningful keywords from *text*.

        Uses NLTK when available; falls back to simple split/filter.
        """
        if _NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text.lower())
                stop_words = set(stopwords.words("english"))
                return [t for t in tokens if t.isalpha() and t not in stop_words]
            except Exception:
                pass

        # Fallback: split and filter short tokens / common words
        _STOPWORDS = {
            "the", "a", "an", "is", "are", "was", "be", "to", "of",
            "and", "in", "it", "i", "you", "me", "my", "we", "do",
        }
        return [
            w.lower() for w in text.split()
            if len(w) > 2 and w.lower() not in _STOPWORDS
        ]

    def process(self, text: str) -> Dict[str, object]:
        """
        Process *text* and return a dict with ``intent`` and ``keywords``.
        """
        return {
            "raw": text,
            "intent": self.detect_intent(text),
            "keywords": self.extract_keywords(text),
        }
