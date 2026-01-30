from __future__ import annotations

import re

from utils.nimbus_state import DAYS


def detect_intent(text: str) -> str:
    """Very small intent router: weather vs calendar vs unknown."""
    t = text.lower()

    if any(
        w in t
        for w in [
            "calendar",
            "appointment",
            "meeting",
            "schedule",
            "event",
            "add",
            "create",
            "delete",
            "remove",
            "update",
            "change",
            "where is my next",
            "next appointment",
            "next meeting",
            "next event",
        ]
    ):
        return "calendar"

    if any(
        w in t
        for w in [
            "weather",
            "forecast",
            "temperature",
            "rain",
            "snow",
            "cloud",
            "mist",
            "thunderstorm",
            "sunny",
            "clear",
        ]
    ):
        return "weather"

    if re.search(r"\bnext\s+(\d+|one|two|three|four|five|six|seven)\s+days\b", t):
        return "weather"

    if any(w in t for w in (["today", "tomorrow", "there"] + DAYS)):
        return "weather"

    return "unknown"
