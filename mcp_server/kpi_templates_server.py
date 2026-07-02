"""MCP server exposing governed KPI playbooks to external agent clients."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from tools.rag_tools import retrieve_kpi_context

mcp = FastMCP("insight-hive-kpi-playbooks")


@mcp.tool()
def get_industry_kpi_playbook(industry: str, question: str = "") -> dict:
    """Return grounded KPI definitions and guardrails for an industry."""
    return json.loads(retrieve_kpi_context(industry, question))


@mcp.resource("kpi://industries")
def list_industries() -> str:
    """List industries currently covered by the local KPI knowledge base."""
    return json.dumps(
        {"industries": ["hr", "marketing", "operations", "retail", "saas"]}
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
