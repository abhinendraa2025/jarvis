"""
Web search module for JARVIS.

Uses the DuckDuckGo Instant Answer API (no API key required).
"""

from __future__ import annotations

import logging
import re
import urllib.parse

import requests  # type: ignore

logger = logging.getLogger(__name__)

_DDG_URL = "https://api.duckduckgo.com/"
_TIMEOUT = 8  # seconds


def _extract_query(text: str) -> str:
    """Strip command words to extract the actual search query."""
    patterns = [
        r"(?:search|look up|find|google|search for)\s+(?:for\s+)?(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text.strip()


def handle_search(text: str) -> str:
    """
    Perform a web search and return a human-readable summary.

    Args:
        text: Raw user utterance containing the search request.

    Returns:
        Summary string from DuckDuckGo, or a helpful error message.
    """
    query = _extract_query(text)
    if not query:
        return "What would you like me to search for?"

    logger.info("Searching for: %s", query)

    try:
        params = {
            "q": query,
            "format": "json",
            "no_redirect": "1",
            "no_html": "1",
            "skip_disambig": "1",
        }
        response = requests.get(_DDG_URL, params=params, timeout=_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # Use Abstract if available
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            source = data.get("AbstractSource", "")
            url = data.get("AbstractURL", "")
            result = abstract
            if source:
                result += f" (Source: {source})"
            if url:
                result += f"\nURL: {url}"
            return result

        # Fall back to Answer
        answer = data.get("Answer", "").strip()
        if answer:
            return answer

        # Fall back to Related Topics
        topics = data.get("RelatedTopics", [])
        if topics:
            first = topics[0]
            if isinstance(first, dict):
                snippet = first.get("Text", "").strip()
                if snippet:
                    return f"Here's what I found: {snippet}"

        encoded = urllib.parse.quote_plus(query)
        return (
            f"I couldn't find a direct answer for '{query}'. "
            f"You can search manually at: https://duckduckgo.com/?q={encoded}"
        )

    except requests.exceptions.Timeout:
        logger.warning("Search timed out for query: %s", query)
        return "The search request timed out. Please check your internet connection."
    except requests.exceptions.ConnectionError:
        logger.warning("No internet connection for search.")
        return "I couldn't connect to the internet to search."
    except Exception as exc:
        logger.error("Search error: %s", exc)
        return f"An error occurred while searching: {exc}"
