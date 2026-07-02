from services.mission_rubric import evaluate_mission_success


MISSION = (
    "Analyze risks, forecast revenue, prepare an executive report, "
    "and verify the approval gate."
)
COLUMNS = ["Parsed_Date", "Revenue", "Region"]
REQUIRED_TOOLS = [
    "run_full_analysis_pipeline",
    "mcp_get_industry_kpi_playbook",
    "run_forecast",
    "get_business_context_snapshot",
    "check_publish_gate",
]


def test_complete_mission_requires_all_objective_evidence():
    result = evaluate_mission_success(MISSION, COLUMNS, REQUIRED_TOOLS)
    assert result["completed"] is True
    assert result["success_score"] == 100
    assert result["criteria_passed"] == result["criteria_total"] == 5


def test_missing_forecast_cannot_be_marked_complete():
    tools = [tool for tool in REQUIRED_TOOLS if tool != "run_forecast"]
    result = evaluate_mission_success(MISSION, COLUMNS, tools)
    assert result["completed"] is False
    assert result["success_score"] < 100
    assert result["success_criteria"]["Forward-looking forecast"] is False


def test_agent_error_cannot_be_marked_complete_even_with_tools():
    result = evaluate_mission_success(
        MISSION,
        COLUMNS,
        REQUIRED_TOOLS,
        "ADK agent error: quota exhausted",
    )
    assert result["completed"] is False
