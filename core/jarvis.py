"""
Core JARVIS class – orchestrates speech, NLP, modules, and database.
"""

from __future__ import annotations

import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Callable, Dict, List, Optional

from config.settings import settings
from core.nlp import NLPProcessor
from core.speech import SpeechEngine
from utils.helpers import format_timestamp, truncate

logger = logging.getLogger(__name__)


class Jarvis:
    """
    Central JARVIS AI Assistant class.

    Responsibilities
    ----------------
    * Accept text or voice input.
    * Detect intent via :class:`~core.nlp.NLPProcessor`.
    * Route to the appropriate command handler.
    * Deliver responses via :class:`~core.speech.SpeechEngine` and/or
      return them as strings (for the web UI).
    * Persist conversation history in SQLite.
    """

    def __init__(self, speech_enabled: bool = True):
        self._speech_enabled = speech_enabled
        self._nlp = NLPProcessor()
        self._speech = SpeechEngine(
            rate=settings.SPEECH_RATE,
            volume=settings.SPEECH_VOLUME,
            voice_index=settings.SPEECH_VOICE_INDEX,
        )
        self._handlers: Dict[str, Callable[[str], str]] = {}
        self._running = False

        self._init_database()
        self._register_default_handlers()
        logger.info("%s initialised.", settings.JARVIS_NAME)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    def _init_database(self):
        """Create the conversation history table if it does not exist."""
        try:
            db_path = Path(settings.DATABASE_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id        INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT    NOT NULL,
                        speaker   TEXT    NOT NULL,
                        message   TEXT    NOT NULL
                    )
                    """
                )
                conn.commit()
            logger.debug("Database ready at %s", db_path)
        except Exception as exc:
            logger.error("Database init failed: %s", exc)

    def _save_message(self, speaker: str, message: str):
        try:
            with sqlite3.connect(settings.DATABASE_PATH) as conn:
                conn.execute(
                    "INSERT INTO conversations (timestamp, speaker, message) VALUES (?, ?, ?)",
                    (format_timestamp(), speaker, message),
                )
                conn.commit()
        except Exception as exc:
            logger.error("Failed to save message: %s", exc)

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Return the last *limit* conversation entries."""
        try:
            with sqlite3.connect(settings.DATABASE_PATH) as conn:
                cursor = conn.execute(
                    "SELECT timestamp, speaker, message FROM conversations "
                    "ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
                rows = cursor.fetchall()
            return [
                {"timestamp": r[0], "speaker": r[1], "message": r[2]}
                for r in reversed(rows)
            ]
        except Exception as exc:
            logger.error("Failed to load history: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def register_handler(self, intent: str, handler: Callable[[str], str]):
        """Register a callable for a given *intent* name."""
        self._handlers[intent] = handler
        logger.debug("Handler registered for intent '%s'.", intent)

    def _register_default_handlers(self):
        """Wire up built-in command handlers."""
        # Lazy imports to avoid pulling in all modules at startup
        from modules.calculator import handle_calculate
        from modules.web_search import handle_search
        from modules.system import handle_system_info

        self.register_handler("greeting", self._handle_greeting)
        self.register_handler("farewell", self._handle_farewell)
        self.register_handler("thanks", self._handle_thanks)
        self.register_handler("time", self._handle_time)
        self.register_handler("date", self._handle_date)
        self.register_handler("joke", self._handle_joke)
        self.register_handler("help", self._handle_help)
        self.register_handler("calculate", handle_calculate)
        self.register_handler("search", handle_search)
        self.register_handler("system_info", handle_system_info)

    # ------------------------------------------------------------------
    # Built-in handlers
    # ------------------------------------------------------------------

    def _handle_greeting(self, _text: str) -> str:
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        return f"{greeting}! I'm {settings.JARVIS_NAME}. How can I help you?"

    def _handle_farewell(self, _text: str) -> str:
        self._running = False
        return "Goodbye! Have a great day!"

    def _handle_thanks(self, _text: str) -> str:
        return "You're welcome! Is there anything else I can help you with?"

    def _handle_time(self, _text: str) -> str:
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}."

    def _handle_date(self, _text: str) -> str:
        today = datetime.date.today()
        return f"Today is {today.strftime('%A, %B %d, %Y')}."

    def _handle_joke(self, _text: str) -> str:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the programmer quit his job? Because he didn't get arrays!",
            "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
            "Why do Python programmers prefer dark mode? Because light attracts bugs!",
        ]
        import random
        return random.choice(jokes)

    def _handle_help(self, _text: str) -> str:
        return (
            "I can help you with:\n"
            "  • Greetings and small talk\n"
            "  • Telling the time and date\n"
            "  • Web searches (say 'search for <topic>')\n"
            "  • Calculations (say 'calculate 2 + 2')\n"
            "  • System information\n"
            "  • Jokes\n"
            "Just speak or type your request!"
        )

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process(self, text: str) -> str:
        """
        Process a user utterance and return the response text.

        Args:
            text: User input string.

        Returns:
            JARVIS response string.
        """
        if not text or not text.strip():
            return "I didn't catch that. Could you repeat?"

        text = text.strip()
        logger.info("Processing: %s", truncate(text))
        self._save_message("user", text)

        result = self._nlp.process(text)
        intent = result["intent"]
        logger.debug("Intent detected: %s", intent)

        handler = self._handlers.get(intent)
        if handler:
            response = handler(text)
        else:
            response = (
                f"I'm not sure how to help with that yet. "
                f"You said: \"{truncate(text, 80)}\". "
                "Try asking for 'help' to see what I can do."
            )

        logger.info("Response: %s", truncate(response))
        self._save_message("jarvis", response)
        return response

    def respond(self, text: str) -> str:
        """Process *text* and also speak the response (when TTS is available)."""
        response = self.process(text)
        if self._speech_enabled:
            self._speech.speak(response)
        return response

    def listen(self) -> Optional[str]:
        """Listen for a voice command and return the recognised text."""
        return self._speech.listen()

    def listen_and_respond(self) -> Optional[str]:
        """
        Listen for a voice command, process it, and speak the response.

        Returns:
            The JARVIS response string, or *None* if nothing was heard.
        """
        text = self._speech.listen()
        if text:
            return self.respond(text)
        return None

    # ------------------------------------------------------------------
    # Interactive loop
    # ------------------------------------------------------------------

    def run_interactive(self, use_voice: bool = False):
        """
        Start a simple command-line interaction loop.

        Args:
            use_voice: If *True*, use microphone input; otherwise use stdin.
        """
        self._running = True
        print(f"\n{'='*50}")
        print(f"  {settings.JARVIS_NAME} v{settings.JARVIS_VERSION}")
        print("  Type 'quit' or 'exit' to stop.")
        print(f"{'='*50}\n")

        self.respond("Hello! I'm JARVIS. How can I help you?")

        while self._running:
            try:
                if use_voice:
                    print("\nListening… (speak now)")
                    response = self.listen_and_respond()
                    if response is None:
                        print("(nothing heard)")
                else:
                    user_input = input("You: ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("quit", "exit"):
                        self.respond("Goodbye!")
                        break
                    self.respond(user_input)
            except KeyboardInterrupt:
                print("\nInterrupted.")
                self.respond("Goodbye!")
                break
            except EOFError:
                break
