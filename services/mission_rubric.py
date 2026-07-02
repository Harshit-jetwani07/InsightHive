"""Deterministic evidence rubric for autonomous ADK missions."""

from __future__ import annotations

from collections.abc import Iterable


def evaluate_mission_success(
    mission: str,
    columns: Iterable[str],
    selected_tools: Iterable[str],
    response: str = "",
) -> dict:
    """Score whether objective-specific mission evidence was actually produced."""
    objective = (mission or "").lower()
    column_set = set(columns)
    tool_set = set(selected_tools)
    lowered_columns = {str(column).lower() for column in column_set}
    supports_forecast = (
        any(
            token in str(column).lower()
            for column in column_set
            for token in ("date", "time", "month", "year")
        )
        and bool(lowered_columns.intersection({"revenue", "sales", "profit", "amount", "value"}))
    )
    criteria = {
        "Verified dataset analysis": bool(
            tool_set.intersection(
                {
                    "run_full_analysis_pipeline",
                    "get_dataset_overview",
                    "get_summary_statistics",
                }
            )
        ),
        "Industry-grounded recommendations": bool(
            tool_set.intersection(
                {"mcp_get_industry_kpi_playbook", "retrieve_kpi_context"}
            )
        ),
    }
    if supports_forecast and any(
        term in objective for term in ("forecast", "future", "predict", "next")
    ):
        criteria["Forward-looking forecast"] = "run_forecast" in tool_set
    if any(term in objective for term in ("report", "executive", "brief")):
        criteria["Report context prepared"] = "get_business_context_snapshot" in tool_set
    if any(term in objective for term in ("approval", "governance", "publish")):
        criteria["Human approval gate verified"] = bool(
            tool_set.intersection({"check_publish_gate", "submit_for_admin_review"})
        )

    passed = sum(criteria.values())
    total = len(criteria)
    score = round(100 * passed / max(total, 1))
    completed = bool(tool_set) and score == 100 and not (response or "").startswith(
        "ADK agent error:"
    )
    return {
        "success_score": score,
        "criteria_passed": passed,
        "criteria_total": total,
        "success_criteria": criteria,
        "completed": completed,
    }
