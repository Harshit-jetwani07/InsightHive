"""Provider key detection without assuming one historical Google key prefix."""


def is_gemini_key(value: str | None) -> bool:
    """Recognize both legacy AIza and newer AQ-prefixed Gemini API keys."""
    key = (value or "").strip()
    return len(key) >= 20 and key.startswith(("AIza", "AQ"))
