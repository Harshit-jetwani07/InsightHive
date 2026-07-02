"""Deterministic orchestration tools for reproducible analysis pipelines."""

from __future__ import annotations

import json
import time

from tools.analytics_tools import get_correlation_insights, get_summary_statistics
from tools.data_tools import detect_anomaly_records, evaluate_data_quality, get_dataset_overview


def run_full_analysis_pipeline(include_anomalies: bool = True) -> str:
    """Run overview, quality, analytics, and anomaly stages in a fixed order.

    Args:
        include_anomalies: Whether to run anomaly detection after quality checks.

    Returns:
        JSON containing every stage, duration, and overall status.
    """
    started = time.perf_counter()
    stages: list[dict] = []
    functions = [
        ("ingestion_context", get_dataset_overview),
        ("quality_gate", evaluate_data_quality),
        ("summary_statistics", get_summary_statistics),
        ("correlation_analysis", get_correlation_insights),
    ]
    if include_anomalies:
        functions.append(("anomaly_detection", detect_anomaly_records))

    for name, function in functions:
        stage_started = time.perf_counter()
        try:
            result = json.loads(function())
            status = "error" if "error" in result else "success"
        except Exception as exc:
            result, status = {"error": str(exc)}, "error"
        stages.append(
            {
                "stage": name,
                "status": status,
                "latency_ms": round((time.perf_counter() - stage_started) * 1000),
                "result": result,
            }
        )
        if status == "error":
            break

    return json.dumps(
        {
            "pipeline": "governed_business_analysis",
            "status": "success" if all(s["status"] == "success" for s in stages) else "error",
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "stages": stages,
        },
        indent=2,
        default=str,
    )
