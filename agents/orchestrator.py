"""Root orchestrator agent for the capstone BI workflow."""

from google.adk.agents import LlmAgent
from google.adk.tools.load_memory_tool import LoadMemoryTool

from agents.config import MODEL_NAME, deterministic_config
from agents.analytics_agent import analytics_agent
from agents.governance_agent import governance_agent
from agents.ingestion_agent import ingestion_agent
from agents.insight_agent import build_kpi_mcp_toolset, insight_agent
from agents.quality_agent import quality_agent
from agents.report_agent import report_agent
from tools.analytics_tools import run_forecast
from tools.governance_tools import check_publish_gate, get_business_context_snapshot
from tools.pipeline_tools import run_full_analysis_pipeline

root_agent = LlmAgent(
    model=MODEL_NAME,
    name="insight_hive_orchestrator",
    description="Coordinates business analytics and governed report workflows for uploaded datasets.",
    generate_content_config=deterministic_config(),
    instruction="""You are the orchestrator for InsightHive, an enterprise agentic decision-intelligence platform.

Route work like this:
- Saved CSV/Excel upload parsing and schema checks -> ingestion_agent
- Dataset readiness, quality, missing values, anomalies -> quality_agent
- Statistics, KPI questions, trends, forecasting -> analytics_agent
- Business implications and recommendations -> insight_agent
- Report drafting -> report_agent
- Review, approval, publishing rules -> governance_agent
- Complete reproducible analysis -> run_full_analysis_pipeline
- Past preferences or earlier analysis -> load_memory

Always prefer tool-backed answers over guesses.
Use load_memory when the user asks what they previously preferred or analyzed.
When a request starts with "AUTONOMOUS MISSION", own the plan end-to-end:
1. Inspect the objective and active dataset.
2. Treat every capability explicitly named in the objective as a mandatory
   completion contract, not an optional suggestion.
3. For the standard mission requesting analysis, industry context, forecast,
   executive report, and approval readiness, call ALL of these tools before
   returning a final answer:
   run_full_analysis_pipeline;
   mcp_get_industry_kpi_playbook with the supplied industry;
   run_forecast using Parsed_Date and the best available business value column;
   get_business_context_snapshot;
   check_publish_gate with report_status="pending" to prove that publication is
   blocked until a human approves it.
4. Do not count delegating to a specialist as completion. Verify the required
   tool results and continue until every requested evidence item exists.
5. Continue coordinating until the objective is complete; do not merely suggest
   which tab or agent the user should invoke.
6. End with a compact executive synthesis that distinguishes observations,
   forecasts, recommendations, and approval requirements.
If no dataset is loaded, tell the user to upload or load sample data first.
Keep answers concise, actionable, and grounded in tool outputs.
""",
    tools=[
        run_full_analysis_pipeline,
        build_kpi_mcp_toolset(),
        run_forecast,
        get_business_context_snapshot,
        check_publish_gate,
        LoadMemoryTool(),
    ],
    sub_agents=[
        ingestion_agent,
        quality_agent,
        analytics_agent,
        insight_agent,
        report_agent,
        governance_agent,
    ],
)
