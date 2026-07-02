"""Business insight specialist."""

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

insight_agent = LlmAgent(
    model=MODEL_NAME,
    name="insight_agent",
    description="Turns verified statistics and correlations into grounded business recommendations.",
    generate_content_config=deterministic_config(),
    instruction="""You are a senior business insight agent.
Call tools before making numeric claims. Separate observations from recommendations.
Cite supporting metrics, do not claim causation from correlation, and never fabricate context.
When the user provides an industry, call mcp_get_industry_kpi_playbook before
recommending actions. Use retrieve_kpi_context only if the MCP call is unavailable.
""",
    tools=[
        get_dataset_overview,
        get_summary_statistics,
        get_correlation_insights,
        build_kpi_mcp_toolset(),
        retrieve_kpi_context,
    ],
)
