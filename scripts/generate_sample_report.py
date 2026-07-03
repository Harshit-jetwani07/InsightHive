"""Generate the repository's reviewable sample PDF without external AI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.sample_data import build_retail_demo_dataset
from utils.report_generator import ReportGenerator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="submission/evidence/sample_approved_business_report.pdf",
    )
    args = parser.parse_args()

    df = build_retail_demo_dataset()
    sections = {
        "executive_summary": (
            "Northstar Retail's sample workspace contains 1,664 weekly product and "
            "regional records designed to demonstrate a complete governed analysis. "
            "The data is structurally ready for decision support and contains clear "
            "signals across revenue, profit, target achievement, returns, customer "
            "satisfaction, and marketing spend. Management should use this report to "
            "identify where growth is healthy, where margin or return-rate pressure "
            "needs investigation, and which findings require human review before action."
        ),
        "key_insights": (
            "The strongest business story is not revenue growth alone, but the balance "
            "between growth, profitability, returns, and customer experience. Higher "
            "sales or marketing activity should be reviewed alongside profit margin and "
            "target achievement so that volume does not hide weak economics. The sample "
            "also contains explainable regional and product-level risk signals, including "
            "elevated return pressure in selected segments. These patterns identify where "
            "a manager should investigate first; they do not prove a single root cause."
        ),
        "recommendations": (
            "First, review the highest-severity unusual records and confirm whether they "
            "represent genuine campaigns, operational exceptions, or data-entry issues. "
            "Second, compare revenue growth with profit margin and return rate by region "
            "and product before moving budget. Third, investigate customer dissatisfaction "
            "where returns remain elevated and assign an owner to each corrective action. "
            "Finally, compare each forecast period with actual performance and revise the "
            "plan when error moves outside the organization's accepted range."
        ),
        "limitations": (
            "This report is based only on the active sample dataset and does not include "
            "external market conditions, competitor activity, inventory constraints, or "
            "management explanations that were not recorded in the file. Forecasts show "
            "a likely direction rather than a guaranteed outcome, and relationships in "
            "the data do not establish cause and effect. The report therefore remains "
            "decision support: an authorized human reviewer must confirm the evidence, "
            "business context, and recommended actions before publication."
        ),
    }
    generator = ReportGenerator(
        df=df,
        ai_agent=None,
        analyzer=None,
        company_name="Northstar Retail",
        analyst_name="InsightHive Agent",
        report_title="Governed Retail Decision Brief",
        report_date="2026-07-03",
        filename="northstar_retail_demo.csv",
        report_sections=sections,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(generator.generate())
    print(output.resolve())


if __name__ == "__main__":
    main()
