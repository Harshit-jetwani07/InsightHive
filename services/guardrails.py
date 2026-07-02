"""Input guardrails for the agent boundary."""

from __future__ import annotations

import re

_INJECTION_PATTERNS = [
    r"\bignore (all |any |the )?(previous|prior|system|developer) instructions?\b",
    r"\breveal (the )?(system|developer) prompt\b",
    r"\bprint (your )?(hidden|system|developer) instructions?\b",
    r"\bbypass (the )?(guardrails?|security|approval)\b",
    r"\bpretend (that )?you have admin\b",
]


def validate_user_question(question: str) -> tuple[bool, str]:
    """Validate user input before it reaches an LLM."""
    cleaned = (question or "").strip()
    if not cleaned:
        return False, "Please enter a question."
    if len(cleaned) > 4000:
        return False, "Question is too long. Keep it under 4,000 characters."
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            return False, "Request blocked by the prompt-injection guardrail."
    return True, ""
