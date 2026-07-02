import json

from services.report_contract import parse_report_sections
from utils.report_generator import ReportGenerator


def test_valid_report_contract_is_accepted():
    payload = {
        "executive_summary": "This executive summary contains grounded business context and enough words for review.",
        "key_insights": "Verified metrics reveal meaningful regional performance differences requiring focused operational investigation now.",
        "recommendations": "Prioritize the weakest segment, monitor margin and returns, and protect the strongest channel.",
        "limitations": "These findings depend on source quality, observed history, and non-causal statistical relationships.",
    }
    sections, error = parse_report_sections(json.dumps(payload))
    assert error == ""
    assert sections == payload


def test_incomplete_report_contract_is_rejected():
    sections, error = parse_report_sections('{"executive_summary": "too short"}')
    assert sections is None
    assert "executive_summary" in error


def test_adk_report_sections_never_call_legacy_author():
    class ExplodingLegacyAuthor:
        def generate_report_text(self, *_args, **_kwargs):
            raise AssertionError("Legacy report author must never run in ADK mode.")

    sections = {
        "executive_summary": "Validated executive summary.",
        "key_insights": "Validated key insights.",
        "recommendations": "Validated recommendations.",
        "limitations": "Validated limitations.",
    }
    generator = ReportGenerator(
        df=None,
        ai_agent=ExplodingLegacyAuthor(),
        analyzer=None,
        company_name="Test",
        analyst_name="Agent",
        report_title="Test",
        report_date="2026-07-02",
        filename="test.csv",
        report_sections=sections,
    )
    assert generator._agent_section("EXECUTIVE_SUMMARY") == sections["executive_summary"]
