"""Optional Gemini rubric judge for generated business answers."""

from __future__ import annotations

import json
import re

from tools.data_tools import get_dataset_overview
from tools.validation_tools import validate_numeric_grounding
from services.api_keys import is_gemini_key


def _deterministic_judge(response: str, note: str = "") -> dict:
    grounding = json.loads(validate_numeric_grounding(response))
    words = response.split()
    has_action = any(
        token in response.lower()
        for token in ("recommend", "action", "improve", "investigate", "track", "prioritize")
    )
    has_uncertainty = any(
        token in response.lower()
        for token in ("may", "could", "uncertain", "correlation", "sample", "observed")
    )
    claim_count = grounding["claim_count"]
    grounding_score = (
        3
        if claim_count == 0
        else max(1, min(5, round(grounding["grounding_rate"] / 20)))
    )
    usefulness = max(1, min(5, 2 + int(len(words) >= 35) + int(has_action)))
    actionability = 4 if has_action else 2
    uncertainty = 4 if has_uncertainty else 2
    scores = [grounding_score, usefulness, actionability, uncertainty]
    return {
        "mode": "deterministic_fallback",
        "factual_grounding": grounding_score,
        "business_usefulness": usefulness,
        "actionability": actionability,
        "uncertainty_handling": uncertainty,
        "overall_score": round(sum(scores) / len(scores), 2),
        "grounding_rate": grounding["grounding_rate"],
        "unsupported_claims": grounding["unsupported_claims"][:10],
        "rationale": (
            "Scored locally from numeric grounding, response depth, action language, "
            "and uncertainty language."
        ),
        "note": note,
    }


def judge_business_response(response: str, api_key: str) -> dict:
    """Score an answer for grounding, usefulness, and actionability."""
    if not response.strip():
        return {"error": "Enter an agent response to evaluate."}
    if not is_gemini_key(api_key):
        return _deterministic_judge(response)

    from google import genai

    context = get_dataset_overview()
    prompt = f"""Act as a strict evaluator. Score the business answer from 1 to 5
for factual_grounding, business_usefulness, actionability, and uncertainty_handling.
Use only the dataset context below. Return JSON only, with those four integer keys,
an overall_score number, and a short rationale.

DATASET CONTEXT:
{context}

ANSWER:
{response[:6000]}
"""
    try:
        client = genai.Client(api_key=api_key.strip())
        result = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )
    except Exception as exc:
        return _deterministic_judge(response, note=f"Gemini unavailable: {exc}")
    text = (result.text or "").strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return _deterministic_judge(response, note="Gemini judge returned non-JSON output.")
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return _deterministic_judge(response, note="Gemini judge returned malformed JSON.")
    payload["mode"] = "gemini_llm_judge"
    return payload
