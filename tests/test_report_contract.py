import json

import pandas as pd

from services.report_contract import parse_report_sections
from utils.report_generator import ReportGenerator


def test_valid_report_contract_is_accepted():
    section = (
        "This section explains the verified business evidence in clear language for "
        "a manager, describes why the measured pattern matters, identifies the main "
        "risk, recommends a practical next action, and reminds the reader that the "
        "available dataset and human review determine how confidently the result can "
        "be used for an operational decision."
    )
    payload = {
        "executive_summary": section,
        "key_insights": section,
        "recommendations": section,
        "limitations": section,
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


def test_business_report_has_cover_and_multiple_readable_content_pages():
    class NoLegacyAuthor:
        pass

    section = (
        "This verified section gives management a clear explanation of current "
        "performance, the business meaning of the observed figures, the most important "
        "risk to review, a practical next action, and an honest limitation. It uses "
        "plain language so the evidence can support a responsible human decision "
        "without presenting a forecast or relationship as a guaranteed outcome."
    )
    generator = ReportGenerator(
        df=pd.DataFrame(
            {
                "Revenue": [100.0, 120.0, 115.0, 130.0],
                "Profit": [12.0, 15.0, 13.0, 18.0],
                "Region": ["North", "South", "North", "West"],
            }
        ),
        ai_agent=NoLegacyAuthor(),
        analyzer=None,
        company_name="Test Company",
        analyst_name="InsightHive",
        report_title="Business Performance Report",
        report_date="2026-07-03",
        filename="sample.csv",
        report_sections={
            "executive_summary": section,
            "key_insights": section,
            "recommendations": section,
            "limitations": section,
        },
    )
    pdf = generator.generate()
    page_count = pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages")
    assert pdf.startswith(b"%PDF")
    assert page_count >= 4
