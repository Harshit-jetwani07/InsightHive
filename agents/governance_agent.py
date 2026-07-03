"""Human-in-the-loop governance specialist."""

from google.adk.agents import LlmAgent

from agents.config import MODEL_NAME, deterministic_config
from tools.governance_tools import (
    check_publish_gate,
    get_business_context_snapshot,
    submit_for_admin_review,
)

governance_agent = LlmAgent(
    model=MODEL_NAME,
    name="governance_agent",
    description="Enforces report review gates and explains pending approval status.",
    generate_content_config=deterministic_config(),
    instruction="""You are the governance agent.
Submit only when explicitly requested. A pending report is never approved or publishable.
For every question about whether publication or download is allowed, you MUST
call check_publish_gate and ground the answer in that result.
Use concise audit-friendly language and return the report identifier and status.
""",
    tools=[check_publish_gate, get_business_context_snapshot, submit_for_admin_review],
)
