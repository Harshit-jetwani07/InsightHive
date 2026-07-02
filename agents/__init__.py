"""Google ADK agent definitions for the capstone project."""

from agents.analytics_agent import analytics_agent
from agents.governance_agent import governance_agent
from agents.insight_agent import insight_agent
from agents.ingestion_agent import ingestion_agent
from agents.quality_agent import quality_agent
from agents.report_agent import report_agent
from agents.orchestrator import root_agent

__all__ = [
    "analytics_agent",
    "governance_agent",
    "insight_agent",
    "ingestion_agent",
    "quality_agent",
    "report_agent",
    "root_agent",
]
