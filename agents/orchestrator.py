"""Root orchestrator agent for the capstone BI workflow."""

from google.adk.agents import LlmAgent
from google.adk.tools.load_memory_tool import LoadMemoryTool

from agents.config import MODEL_NAME, deterministic_config
from agents.analytics_agent import analytics_agent
from agents.governance_agent import governance_agent
from agents.ingestion_agent import ingestion_agent
from agents.insight_agent import build_kpi_mcp_toolset, insight_agent, live_mcp_enabled
from agents.quality_agent import quality_agent
from agents.report_agent import report_agent
from tools.analytics_tools import run_forecast
from tools.governance_tools import check_publish_gate, get_business_context_snapshot
from tools.pipeline_tools import run_full_analysis_pipeline
from tools.rag_tools import retrieve_kpi_context


def _fresh_specialist(agent: LlmAgent) -> LlmAgent:
    """Clone a specialist so ADK can attach it to a new root safely."""
    clone = agent.model_copy(deep=False)
    clone.parent_agent = None
    return clone


def build_root_agent() -> LlmAgent:
    """Build an isolated root runtime for each provider-key attempt.

    ADK agents and MCP toolsets retain runtime/session state. Rebuilding them is
    required when failover switches the Gemini project behind an API key.
    """
    mcp_enabled = live_mcp_enabled()
    industry_tool_rule = (
        "- industry KPI playbooks -> call mcp_get_industry_kpi_playbook;"
        if mcp_enabled
        else "- industry KPI playbooks -> call retrieve_kpi_context;"
    )
    standard_industry_step = (
        "mcp_get_industry_kpi_playbook with the supplied industry;"
        if mcp_enabled
        else "retrieve_kpi_context with the supplied industry;"
    )
    grounding_label = (
        "the live MCP playbook"
        if mcp_enabled
        else "the local KPI playbook retrieval fallback"
    )
    grounding_tools = [build_kpi_mcp_toolset()] if mcp_enabled else [retrieve_kpi_context]

    return LlmAgent(
        model=MODEL_NAME,
        name="insight_hive_orchestrator",
        description="Coordinates business analytics and governed report workflows for uploaded datasets.",
        generate_content_config=deterministic_config(),
        instruction=f"""You are the orchestrator for InsightHive, an enterprise agentic decision-intelligence platform.

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
For every dataset question, a plain-text answer without a completed business
tool call is invalid. Route and execute according to these mandatory rules:
- readiness, missing values, or quality -> quality_agent, which must call
  evaluate_data_quality;
- unusual records, outliers, or anomalies -> quality_agent, which must call
  detect_anomaly_records;
- schema, rows, columns, or available fields -> quality_agent, which must call
  get_dataset_overview;
- numeric KPI summaries or verified statistics -> analytics_agent, which must
  call get_summary_statistics;
- relationships or correlations -> analytics_agent, which must call
  get_correlation_insights;
- forecasts or future periods -> analytics_agent, which must call run_forecast;
{industry_tool_rule}
- executive report context -> report_agent, which must call
  get_business_context_snapshot;
- complete governed analysis -> call run_full_analysis_pipeline;
- publication/download approval -> governance_agent, which must call
  check_publish_gate.
Do not merely explain which tool should be used. Execute it and base the final
answer on its response. Delegation alone is not completion.
For industry grounding, use {grounding_label}. If the hosted runtime is running
in fallback mode, do not claim that a live MCP session was used.
Use load_memory when the user asks what they previously preferred or analyzed.
When a request starts with "AUTONOMOUS MISSION", own the plan end-to-end:
1. Inspect the objective and active dataset.
2. Treat every capability explicitly named in the objective as a mandatory
   completion contract, not an optional suggestion.
3. For the standard mission requesting analysis, industry context, forecast,
   executive report, and approval readiness, call ALL of these tools before
   returning a final answer:
   run_full_analysis_pipeline;
   {standard_industry_step}
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
Write the user-facing answer in normal business language. Explain what happened,
why it matters, and what the user should do next. Avoid internal tool names,
JSON, implementation jargon, and unexplained technical abbreviations outside
the dedicated trace/evidence views. Keep answers concise, actionable, and
grounded in tool outputs.
""",
        tools=[
            run_full_analysis_pipeline,
            *grounding_tools,
            run_forecast,
            get_business_context_snapshot,
            check_publish_gate,
            LoadMemoryTool(),
        ],
        sub_agents=[
            _fresh_specialist(ingestion_agent),
            _fresh_specialist(quality_agent),
            _fresh_specialist(analytics_agent),
            _fresh_specialist(insight_agent),
            _fresh_specialist(report_agent),
            _fresh_specialist(governance_agent),
        ],
    )


root_agent = build_root_agent()
