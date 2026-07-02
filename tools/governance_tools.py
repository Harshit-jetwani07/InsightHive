"""ADK governance and reporting tools."""

from __future__ import annotations

import json

from services.dataset_store import get_current_dataset, require_dataframe
from utils.auth import save_report_record


def check_publish_gate(report_status: str) -> str:
    """Verify whether a report status permits publication or download.

    Args:
        report_status: Current human-review status, such as pending or approved.

    Returns:
        JSON decision proving that only approved reports can be published.
    """
    normalized = (report_status or "").strip().lower()
    allowed = normalized == "approved"
    return json.dumps(
        {
            "report_status": normalized or "unknown",
            "download_allowed": allowed,
            "policy": "Human approval is mandatory before publication or download.",
            "compliant": not allowed if normalized in {"pending", "rejected", "unknown"} else allowed,
        },
        indent=2,
    )


def submit_for_admin_review(report_title: str, revision_of: int = 0) -> str:
    """Submit a generated report title for admin approval before user download.

    Args:
        report_title: Title of the business report awaiting review.
        revision_of: Rejected report id this version revises, or zero for a new report.

    Returns:
        JSON string with report id and pending status.
    """
    ctx = get_current_dataset()
    if not ctx.username:
        return json.dumps({"error": "No active user context for governance workflow."})

    report_id = save_report_record(report_title, ctx.username, revision_of or None)
    payload = {
        "report_id": report_id,
        "title": report_title,
        "status": "pending",
        "revision_of": revision_of or None,
        "message": "Report submitted for admin human-in-the-loop approval.",
    }
    return json.dumps(payload, indent=2)


def get_business_context_snapshot() -> str:
    """Return a compact business context snapshot for report writing agents.

    Returns:
        JSON string with dataset shape, quality, and top-level stats text.
    """
    df, filename = require_dataframe()
    from utils.data_analyzer import DataAnalyzer
    from utils.data_quality import evaluate_dataset_quality

    analyzer = DataAnalyzer(df)
    quality = evaluate_dataset_quality(df)
    payload = {
        "filename": filename,
        "quality_score": quality["score"],
        "quality_grade": quality["grade"],
        "text_summary": analyzer.get_text_summary(),
    }
    return json.dumps(payload, indent=2, default=str)
