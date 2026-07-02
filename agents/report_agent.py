"""Governed report drafting specialist."""

from google.adk.agents import LlmAgent

from agents.config import MODEL_NAME, deterministic_config
from tools.governance_tools import get_business_context_snapshot, submit_for_admin_review
from tools.validation_tools import validate_numeric_grounding

report_agent = LlmAgent(
    model=MODEL_NAME,
    name="report_agent",
    description="Drafts grounded executive report outlines and sends completed reports for review.",
    generate_content_config=deterministic_config(),
    instruction="""You are the report specialist.
Use get_business_context_snapshot before drafting. Include an executive summary,
quality note, evidence-backed findings, recommendations, and limitations.
Only submit when the user explicitly asks. Never describe a pending report as approved.
Validate draft numeric claims with validate_numeric_grounding before submission.
""",
    tools=[
        get_business_context_snapshot,
        validate_numeric_grounding,
        submit_for_admin_review,
    ],
)
