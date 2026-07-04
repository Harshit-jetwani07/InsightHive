"""Business insight specialist."""

import os
import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from agents.config import MODEL_NAME, deterministic_config
from tools.analytics_tools import get_correlation_insights, get_summary_statistics
from tools.data_tools import get_dataset_overview
from tools.rag_tools import retrieve_kpi_context

MCP_SERVER = Path(__file__).resolve().parents[1] / "mcp_server" / "kpi_templates_server.py"


def live_mcp_enabled() -> bool:
    """Return whether the live stdio MCP runtime should be attached.

    Render's free web-service runtime can repeatedly fail to create nested
    stdio MCP sessions. Local Docker keeps the live MCP path enabled by
    default, while Render uses the same KPI knowledge base through the
    deterministic retrieval tool so the public demo stays stable.
    """
    override = os.getenv("ENABLE_LIVE_MCP", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if override in {"0", "false", "no", "off"}:
        return False
    render_runtime = any(
        os.getenv(name)
        for name in ("RENDER", "RENDER_SERVICE_ID", "RENDER_EXTERNAL_URL", "RENDER_SERVICE_NAME")
    )
    return not render_runtime


def build_kpi_mcp_toolset() -> McpToolset:
    """Create an independent MCP connection for an ADK agent."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[str(MCP_SERVER)],
            ),
            timeout=10.0,
        ),
        tool_filter=["get_industry_kpi_playbook"],
        tool_name_prefix="mcp",
    )


def kpi_grounding_tools() -> list:
    """Return safe KPI-grounding tools for the current runtime."""
    if live_mcp_enabled():
        return [build_kpi_mcp_toolset(), retrieve_kpi_context]
    return [retrieve_kpi_context]

insight_agent = LlmAgent(
    model=MODEL_NAME,
    name="insight_agent",
    description="Turns verified statistics and correlations into grounded business recommendations.",
    generate_content_config=deterministic_config(),
    instruction="""You are a senior business insight agent.
Call tools before making numeric claims. Separate observations from recommendations.
Cite supporting metrics, do not claim causation from correlation, and never fabricate context.
When the user provides an industry, ground recommendations through the available
KPI playbook tool before recommending actions. In local Full ADK mode this is
mcp_get_industry_kpi_playbook; in quota/resilience mode use retrieve_kpi_context.
""",
    tools=[
        get_dataset_overview,
        get_summary_statistics,
        get_correlation_insights,
        *kpi_grounding_tools(),
    ],
)
