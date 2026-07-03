"""Data quality and anomaly specialist."""

from google.adk.agents import LlmAgent

from agents.config import MODEL_NAME, deterministic_config
from tools.data_tools import detect_anomaly_records, evaluate_data_quality, get_dataset_overview

quality_agent = LlmAgent(
    model=MODEL_NAME,
    name="quality_agent",
    description="Audits dataset readiness, missing values, duplicates, and anomalous records.",
    generate_content_config=deterministic_config(),
    instruction="""You are the data quality gate for an enterprise BI workflow.
Always inspect the dataset with tools. Never invent a score or anomaly count.
For readiness, missing-value, duplicate, or quality questions you MUST call
evaluate_data_quality. For unusual-record, outlier, or anomaly questions you
MUST call detect_anomaly_records. For schema, row-count, column, or available
field questions you MUST call get_dataset_overview. Never answer these intents
from general knowledge.
Explain the highest-risk issues first and state whether analysis can safely continue.
""",
    tools=[get_dataset_overview, evaluate_data_quality, detect_anomaly_records],
)
