"""
Application settings loaded from environment / .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


class _Settings:
    # General
    JARVIS_NAME: str = os.getenv("JARVIS_NAME", "JARVIS")
    JARVIS_VERSION: str = os.getenv("JARVIS_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Speech
    SPEECH_RATE: int = int(os.getenv("SPEECH_RATE", "150"))
    SPEECH_VOLUME: float = float(os.getenv("SPEECH_VOLUME", "1.0"))
    SPEECH_VOICE_INDEX: int = int(os.getenv("SPEECH_VOICE_INDEX", "0"))

    # Flask / web
    FLASK_HOST: str = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")

    # Database
    DATABASE_PATH: str = str(_ROOT / os.getenv("DATABASE_PATH", "jarvis.db"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = str(_ROOT / os.getenv("LOG_FILE", "jarvis.log"))


settings = _Settings()
