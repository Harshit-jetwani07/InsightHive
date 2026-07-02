"""Deterministic evaluation suite for the active business dataset."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from tools.analytics_tools import get_correlation_insights, get_summary_statistics
from tools.data_tools import detect_anomaly_records, evaluate_data_quality, get_dataset_overview
from tools.pipeline_tools import run_full_analysis_pipeline
from services.api_keys import is_gemini_key

CASES_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "test_cases.json"
ROUTING_CASES_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "routing_cases.json"

TOOL_REGISTRY = {
    "get_dataset_overview": get_dataset_overview,
    "evaluate_data_quality": evaluate_data_quality,
    "get_summary_statistics": get_summary_statistics,
    "get_correlation_insights": get_correlation_insights,
    "detect_anomaly_records": detect_anomaly_records,
    "run_full_analysis_pipeline": run_full_analysis_pipeline,
}


def run_evaluation_suite() -> dict:
    """Run fixed tool-selection and execution checks against the active dataset."""
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = []
    total_started = time.perf_counter()

    for case in cases:
        started = time.perf_counter()
        tool_name = case["expected_tool"]
        function = TOOL_REGISTRY[tool_name]
        try:
            payload = json.loads(function())
            passed = "error" not in payload and all(
                key in payload for key in case.get("required_keys", [])
            )
            error = payload.get("error", "")
        except Exception as exc:
            passed, error = False, str(exc)
        results.append(
            {
                "id": case["id"],
                "scenario": case["scenario"],
                "expected_tool": tool_name,
                "passed": passed,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "error": error,
            }
        )

    passed_count = sum(result["passed"] for result in results)
    return {
        "evaluation_mode": "deterministic_tool_contracts",
        "cases": len(results),
        "passed": passed_count,
        "pass_rate": round(100 * passed_count / max(len(results), 1), 1),
        "latency_ms": round((time.perf_counter() - total_started) * 1000),
        "results": results,
    }


def run_agent_routing_evaluation(api_key: str, user_id: str) -> dict:
    """Send natural-language cases through ADK and score selected tools."""
    from services.agent_runner import get_agent_runner

    if not is_gemini_key(api_key):
        return run_evaluation_suite()

    cases = json.loads(ROUTING_CASES_PATH.read_text(encoding="utf-8"))
    runner = get_agent_runner()
    results = []
    total_started = time.perf_counter()

    for case in cases:
        started = time.perf_counter()
        expected = case["expected_tool"]
        selected_attempts = []
        response = ""
        passed = False
        for attempt in range(1, 3):
            session_id = f"eval-{uuid.uuid4().hex[:10]}"
            question = case["question"]
            if attempt == 2:
                question += (
                    " Retry using the most appropriate available specialist and "
                    "a grounded tool call; do not answer from general knowledge."
                )
            response = runner.run_query(
                question,
                user_id=user_id,
                session_id=session_id,
                api_key=api_key,
            )
            selected_tools = [item["tool"] for item in runner.get_tool_artifacts()]
            selected_attempts.append(selected_tools)
            if expected in selected_tools:
                passed = True
                break
        results.append(
            {
                "id": case["id"],
                "scenario": case["question"],
                "expected_tool": expected,
                "selected_tools": " | ".join(
                    f"attempt {index + 1}: {', '.join(tools) or 'none'}"
                    for index, tools in enumerate(selected_attempts)
                ),
                "attempts": len(selected_attempts),
                "passed": passed,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "error": response if response.startswith("ADK agent error:") else "",
            }
        )

    passed_count = sum(result["passed"] for result in results)
    first_attempt_passed = sum(
        result["passed"] and result["attempts"] == 1 for result in results
    )
    retry_recoveries = sum(
        result["passed"] and result["attempts"] > 1 for result in results
    )
    return {
        "evaluation_mode": "adk_agent_routing",
        "cases": len(results),
        "passed": passed_count,
        "pass_rate": round(100 * passed_count / max(len(results), 1), 1),
        "latency_ms": round((time.perf_counter() - total_started) * 1000),
        "average_case_latency_ms": round(
            sum(result["latency_ms"] for result in results) / max(len(results), 1)
        ),
        "first_attempt_accuracy": round(
            100 * first_attempt_passed / max(len(results), 1), 1
        ),
        "retry_recoveries": retry_recoveries,
        "results": results,
    }
