"""Grounded retrieval over the local KPI playbook knowledge base."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "rag" / "kpi_knowledge"


def retrieve_kpi_context(industry: str, question: str = "") -> str:
    """Retrieve relevant KPI guidance from the local industry knowledge base.

    Args:
        industry: Industry such as retail, SaaS, marketing, operations, or HR.
        question: Optional business question used to rank matching guidance.

    Returns:
        JSON with source file, selected guidance lines, and retrieval score.
    """
    requested = re.sub(r"[^a-z]", "", (industry or "").lower())
    files = list(KNOWLEDGE_DIR.glob("*.md"))
    match = next((path for path in files if path.stem == requested), None)
    if match is None:
        available = sorted(path.stem for path in files)
        return json.dumps({"error": "Unknown industry.", "available_industries": available})

    lines = [
        line[2:].strip()
        for line in match.read_text(encoding="utf-8").splitlines()
        if line.startswith("- ")
    ]
    if question.strip() and lines:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(
            [question] + lines
        )
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        ranked_indices = similarities.argsort()[::-1][:4]
        selected = [lines[index] for index in ranked_indices]
        scores = [round(float(similarities[index]), 4) for index in ranked_indices]
    else:
        selected = lines[:4]
        scores = [0.0 for _ in selected]
    return json.dumps(
        {
            "industry": match.stem,
            "source": str(match.relative_to(KNOWLEDGE_DIR.parent.parent)),
            "retrieval_method": "tfidf_cosine_vector",
            "guidance": selected,
            "similarity_scores": scores,
            "top_match_score": max(scores, default=0.0),
        },
        indent=2,
    )
