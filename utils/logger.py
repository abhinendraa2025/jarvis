"""Logging utility for JARVIS."""

import logging
import logging.handlers
import os
import sys


def setup_logger(name: str, log_file: str = None, level: str = None) -> logging.Logger:
    """
    Create and configure a logger.

    Args:
        name: Logger name (typically ``__name__``).
        log_file: Optional path to a log file; falls back to the value in
                  :pymod:`config.settings` when *None*.
        level: Logging level string (e.g. ``"INFO"``); falls back to settings.

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    # Lazy import to avoid circular imports at module load time
    try:
        from config.settings import settings as _settings

        _level = level or _settings.LOG_LEVEL
        _file = log_file or _settings.LOG_FILE
    except Exception:
        _level = level or "INFO"
        _file = log_file

    numeric_level = getattr(logging, _level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured – return as-is to avoid duplicate handlers
        return logger

    logger.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (optional)
    if _file:
        try:
            os.makedirs(os.path.dirname(_file) or ".", exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                _file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # Never crash the app just because logging setup fails

    return logger
