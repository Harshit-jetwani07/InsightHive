"""Specialist analytics agent with deterministic business intelligence tools."""

from google.adk.agents import LlmAgent

from agents.config import MODEL_NAME, deterministic_config
from tools.analytics_tools import get_correlation_insights, get_summary_statistics, run_forecast
from tools.data_tools import (
    detect_anomaly_records,
    evaluate_data_quality,
    get_dataset_overview,
    parse_uploaded_dataset,
)

analytics_agent = LlmAgent(
    model=MODEL_NAME,
    name="analytics_agent",
    description="Analyzes uploaded business datasets using quality, stats, correlation, anomaly, and forecast tools.",
    generate_content_config=deterministic_config(),
    instruction="""You are InsightHive's expert analytics agent.

Your job is to answer business questions about the currently loaded dataset by calling tools.
Never invent numbers. Always call the appropriate tools before giving numeric claims.

Process:
1. If the user names a saved upload that is not active, call parse_uploaded_dataset.
2. If you need context, call get_dataset_overview first.
3. For data quality questions, call evaluate_data_quality.
4. For outliers, call detect_anomaly_records.
5. For KPI summaries, call get_summary_statistics.
6. For relationships, call get_correlation_insights.
7. For future trends, call run_forecast with valid column names from tool output.

Respond in clear business language with bullet points when helpful.
Mention uncertainty when the dataset is small or quality grade is risky.
""",
    tools=[
        parse_uploaded_dataset,
        get_dataset_overview,
        evaluate_data_quality,
        detect_anomaly_records,
        get_summary_statistics,
        get_correlation_insights,
        run_forecast,
    ],
)
