"""
Speech recognition and text-to-speech synthesis for JARVIS.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------
try:
    import speech_recognition as sr  # type: ignore

    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    logger.warning("SpeechRecognition not installed – voice input disabled.")

try:
    import pyttsx3  # type: ignore

    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed – voice output disabled.")


class SpeechEngine:
    """Handles microphone input and TTS output."""

    def __init__(self, rate: int = 150, volume: float = 1.0, voice_index: int = 0):
        self._rate = rate
        self._volume = volume
        self._voice_index = voice_index

        self._recognizer: Optional[object] = None
        self._tts_engine: Optional[object] = None
        self._tts_lock = threading.Lock()
        self._tts_queue: queue.Queue = queue.Queue()

        self._init_recognizer()
        self._init_tts()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_recognizer(self):
        if _SR_AVAILABLE:
            self._recognizer = sr.Recognizer()
            self._recognizer.dynamic_energy_threshold = True
            logger.debug("Speech recognizer initialised.")

    def _init_tts(self):
        if not _TTS_AVAILABLE:
            return
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            voices = engine.getProperty("voices")
            if voices and self._voice_index < len(voices):
                engine.setProperty("voice", voices[self._voice_index].id)
            self._tts_engine = engine
            logger.debug("TTS engine initialised.")
        except Exception as exc:
            logger.error("TTS init failed: %s", exc)

    # ------------------------------------------------------------------
    # Speech recognition
    # ------------------------------------------------------------------

    def listen(self, timeout: int = 5, phrase_limit: int = 10) -> Optional[str]:
        """
        Listen via microphone and return recognised text, or *None* on failure.

        Args:
            timeout: Seconds to wait for speech to begin.
            phrase_limit: Maximum seconds of speech to capture.

        Returns:
            Recognised text string, or *None*.
        """
        if not _SR_AVAILABLE or self._recognizer is None:
            logger.warning("Speech recognition unavailable.")
            return None

        try:
            with sr.Microphone() as source:
                logger.debug("Adjusting for ambient noise…")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.debug("Listening…")
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )

            text = self._recognizer.recognize_google(audio)
            logger.info("Recognised: %s", text)
            return text
        except sr.WaitTimeoutError:
            logger.debug("Listening timed out.")
        except sr.UnknownValueError:
            logger.debug("Could not understand audio.")
        except sr.RequestError as exc:
            logger.error("Google Speech API error: %s", exc)
        except Exception as exc:
            logger.error("Unexpected speech recognition error: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Text-to-speech
    # ------------------------------------------------------------------

    def speak(self, text: str):
        """
        Convert *text* to speech.  Falls back to a console print when TTS is
        unavailable.
        """
        print(f"JARVIS: {text}")
        if not _TTS_AVAILABLE or self._tts_engine is None:
            return

        with self._tts_lock:
            try:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            except Exception as exc:
                logger.error("TTS speak error: %s", exc)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_speech_available(self) -> bool:
        return _SR_AVAILABLE and self._recognizer is not None

    @property
    def is_tts_available(self) -> bool:
        return _TTS_AVAILABLE and self._tts_engine is not None
