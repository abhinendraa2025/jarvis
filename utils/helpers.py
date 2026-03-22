"""General helper utilities."""

import datetime
import re
import unicodedata


def sanitize_text(text: str) -> str:
    """Remove non-printable characters and normalise unicode."""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"[^\x20-\x7E\n\t]", "", text).strip()


def format_timestamp(dt: datetime.datetime = None) -> str:
    """Return a formatted timestamp string."""
    if dt is None:
        dt = datetime.datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate *text* to *max_length* characters, appending '…' if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def yes_or_no(value: str) -> bool:
    """Return *True* if *value* is a common affirmative string."""
    return value.strip().lower() in {"yes", "y", "sure", "ok", "okay", "yeah", "yep"}
