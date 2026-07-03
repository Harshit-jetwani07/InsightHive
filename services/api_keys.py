"""Provider key detection and ordered Gemini failover candidates."""

from __future__ import annotations

import os


def is_gemini_key(value: str | None) -> bool:
    """Recognize both legacy AIza and newer AQ-prefixed Gemini API keys."""
    key = (value or "").strip()
    return len(key) >= 20 and key.startswith(("AIza", "AQ"))


def gemini_key_candidates(primary: str | None = None) -> list[str]:
    """Return unique configured Gemini keys without exposing their values."""
    candidates = [
        (primary or "").strip(),
        os.getenv("GOOGLE_API_KEY", "").strip(),
        os.getenv("GOOGLE_API_KEY_2", "").strip(),
        os.getenv("GOOGLE_API_KEY_3", "").strip(),
    ]
    unique: list[str] = []
    for key in candidates:
        if is_gemini_key(key) and key not in unique:
            unique.append(key)
    return unique
