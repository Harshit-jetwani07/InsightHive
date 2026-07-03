import json

from services.dataset_store import set_current_dataset
from services.sample_data import build_retail_demo_dataset
from tools.analytics_tools import (
    get_correlation_insights,
    get_summary_statistics,
    run_forecast,
)
from tools.data_tools import (
    detect_anomaly_records,
    evaluate_data_quality,
    get_dataset_overview,
)
from tools.governance_tools import check_publish_gate, get_business_context_snapshot
from tools.pipeline_tools import run_full_analysis_pipeline
from tools.rag_tools import retrieve_kpi_context


def _load_sample():
    df = build_retail_demo_dataset()
    set_current_dataset(df, "northstar_retail_demo.csv", "test-user")
    return df


def test_complete_sample_workflow_produces_real_evidence():
    df = _load_sample()

    overview = json.loads(get_dataset_overview())
    quality = json.loads(evaluate_data_quality())
    statistics = json.loads(get_summary_statistics())
    correlations = json.loads(get_correlation_insights())
    anomalies = json.loads(detect_anomaly_records(max_rows=50))
    forecast = json.loads(run_forecast("Parsed_Date", "Revenue", periods=12))
    pipeline = json.loads(run_full_analysis_pipeline())
    industry = json.loads(retrieve_kpi_context("retail", "revenue returns margin"))
    report_context = json.loads(get_business_context_snapshot())
    pending_gate = json.loads(check_publish_gate("pending"))
    approved_gate = json.loads(check_publish_gate("approved"))

    assert overview["rows"] == len(df)
    assert quality["score"] >= 90
    assert "Revenue" in statistics["numeric_columns"]
    assert correlations["top_correlations"]
    assert anomalies["anomaly_count"] > 0
    assert len(forecast["forecast_points"]) == 12
    assert forecast["trend"]
    assert pipeline["status"] == "success"
    assert industry["industry"] == "retail"
    assert industry["guidance"]
    assert report_context["quality_score"] >= 90
    assert pending_gate["download_allowed"] is False
    assert approved_gate["download_allowed"] is True
