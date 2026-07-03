"""Strict contract between the ADK report agent and deterministic PDF formatter."""

from __future__ import annotations

import json
import re

REQUIRED_SECTIONS = (
    "executive_summary",
    "key_insights",
    "recommendations",
    "limitations",
)


def parse_report_sections(text: str) -> tuple[dict[str, str] | None, str]:
    """Parse and validate the report agent's JSON-only final response."""
    match = re.search(r"\{.*\}", text or "", flags=re.DOTALL)
    if not match:
        return None, "Report Agent did not return a JSON object."
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return None, f"Report Agent JSON is malformed: {exc}"

    sections = {}
    for key in REQUIRED_SECTIONS:
        value = str(payload.get(key, "")).strip()
        if len(value.split()) < 45:
            return None, f"Report section '{key}' is missing or too short."
        sections[key] = value
    return sections, ""
