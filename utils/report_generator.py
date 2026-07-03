import io
import pandas as pd
import numpy as np
import re
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


class ReportGenerator:
    def __init__(self, df, ai_agent, analyzer, company_name, analyst_name,
                 report_title, report_date, filename, revision_notes="",
                 agent_narrative="", report_sections=None):
        self.df = df
        self.ai_agent = ai_agent
        self.analyzer = analyzer
        self.company_name = company_name
        self.analyst_name = analyst_name
        self.report_title = report_title
        self.report_date = report_date
        self.filename = filename
        self.revision_notes = revision_notes
        self.agent_narrative = agent_narrative
        self.report_sections = report_sections

    def _agent_section(self, name: str) -> str:
        if self.report_sections is not None:
            key = {
                "EXECUTIVE_SUMMARY": "executive_summary",
                "KEY_INSIGHTS": "key_insights",
                "RECOMMENDATIONS": "recommendations",
                "LIMITATIONS": "limitations",
            }.get(name)
            if not key or not self.report_sections.get(key):
                raise ValueError(
                    f"Validated Report Agent contract is missing required section: {name}"
                )
            # Hard boundary: an ADK-authored report can never call legacy prose generation.
            return self.report_sections[key]
        if not self.agent_narrative:
            return ""
        markers = ["EXECUTIVE_SUMMARY", "KEY_INSIGHTS", "RECOMMENDATIONS", "LIMITATIONS"]
        marker = re.escape(name)
        following = "|".join(re.escape(item) for item in markers if item != name)
        match = re.search(
            rf"{marker}\s*:\s*(.*?)(?=\n\s*(?:{following})\s*:|\Z)",
            self.agent_narrative,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return match.group(1).strip() if match else ""

    def generate(self) -> bytes:
        if not FPDF_AVAILABLE:
            return self._generate_fallback_pdf("FPDF library missing on system.")
        return self._generate_pdf()

    def _generate_pdf(self) -> bytes:
        try:
            class InsightHivePDF(FPDF):
                def footer(inner_self):
                    inner_self.set_y(-12)
                    inner_self.set_font("Helvetica", "", 8)
                    inner_self.set_text_color(120, 130, 145)
                    inner_self.cell(
                        0,
                        5,
                        f"InsightHive - Human-governed decision support | Page {inner_self.page_no()}",
                        align="C",
                    )

            # Let FPDF handle overflow while major sections retain clear page structure.
            pdf = InsightHivePDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            # Helper to clean characters and strip markdown/layout-breaking text.
            def safe_txt(s):
                if s is None:
                    return ""
                s_str = str(s).strip()
                s_str = s_str.replace("`", "'").replace('"', "'")
                s_str = s_str.replace("$", "USD ").replace("%", " percent")
                s_str = s_str.replace("**", "")
                s_str = s_str.encode("ascii", "ignore").decode("ascii")
                s_str = re.sub(r"[ \t]+", " ", s_str)
                s_str = re.sub(r"\n{3,}", "\n\n", s_str)
                return s_str
            # 
            #  PAGE 1: Corporate Cover Page
            # 
            pdf.add_page()
            pdf.set_fill_color(24, 28, 36)  # Deep Slate Dark Theme
            pdf.rect(0, 0, 210, 297, "F")

            # Solid Top Blue Accent Band
            pdf.set_fill_color(37, 99, 235)
            pdf.rect(0, 0, 210, 8, "F")

            # Main Title Branding
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 22)
            pdf.set_y(105)
            pdf.cell(0, 12, safe_txt(self.report_title).upper(), ln=True, align="C")
            
            # Subtitle
            pdf.set_font("Arial", "", 12)
            pdf.set_text_color(140, 150, 170)
            pdf.cell(0, 10, "Evidence-Based Business Performance Report", ln=True, align="C")
            
            pdf.ln(4)
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(110, 120, 135)
            pdf.cell(0, 6, f"Data Source Master: {safe_txt(self.filename)}", ln=True, align="C")

            # Lower Metadata Info Block
            pdf.set_y(225)
            pdf.set_text_color(210, 215, 225)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 6, f"ORGANIZATION: {safe_txt(self.company_name)}", ln=True, align="C")
            pdf.cell(0, 6, f"LEAD ANALYST: {safe_txt(self.analyst_name)}", ln=True, align="C")
            pdf.cell(0, 6, f"GENERATION DATE: {safe_txt(self.report_date)}", ln=True, align="C")


            # 
            #  BODY PAGES (Content flows naturally now without manual add_page blocks)
            # 
            pdf.add_page()
            pdf.set_text_color(30, 41, 59)
            
            # Global Document Section Header Styling Generator
            def add_section_header(title_text):
                if pdf.get_y() > 235:
                    pdf.add_page()
                pdf.ln(3)
                pdf.set_font("Arial", "B", 14)
                pdf.set_text_color(30, 58, 138)  # Deep Navy Blue
                pdf.cell(0, 8, title_text.upper(), ln=1)
                pdf.set_draw_color(37, 99, 235)  # Royal Accent Line
                pdf.set_line_width(0.5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(3)

            #  SECTION 1: EXECUTIVE SUMMARY
            add_section_header("1. Executive Summary")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(55, 65, 81)
            exec_topic = "Executive Summary Structure Analysis"
            if self.revision_notes:
                exec_topic += f". Address admin revision feedback: {self.revision_notes}"
            exec_text = self._agent_section("EXECUTIVE_SUMMARY")
            if not exec_text:
                exec_text = (
                    self.ai_agent._get_fallback_text("Executive", self.df)
                    if self.agent_narrative
                    else self.ai_agent.generate_report_text(self.df, exec_topic)
                )
            pdf.multi_cell(0, 5.0, safe_txt(exec_text))

            #  SECTION 2: GRANULAR DATA INSIGHTS
            add_section_header("2. Key Findings and Business Meaning")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(55, 65, 81)
            findings_text = self._agent_section("KEY_INSIGHTS")
            if not findings_text:
                findings_text = (
                    self.ai_agent._get_fallback_text("Insights", self.df)
                    if self.agent_narrative
                    else self.ai_agent.generate_report_text(
                        self.df, "Key Business Insights Mathematical Relations"
                    )
                )
            pdf.multi_cell(0, 5.0, safe_txt(findings_text))

            pdf.ln(4)
            pdf.set_fill_color(241, 245, 249)
            pdf.set_text_color(30, 41, 59)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 7, "How management should use these findings", ln=1, fill=True)
            pdf.set_font("Arial", "", 9.5)
            pdf.multi_cell(
                0,
                5.0,
                "Use the measured figures to decide where a closer review is needed. "
                "Compare strong and weak segments on more than one KPI, confirm unusual "
                "records with an operational owner, and do not treat a forecast or "
                "correlation as proof of a guaranteed outcome.",
            )

            # Keep the evidence tables readable and ensure the report contains
            # more than a compressed single content page.
            pdf.add_page()

            #  SECTION 3: DESCRIPTIVE STATISTICAL TABLE
            add_section_header("3. Measured Performance Snapshot")
            pdf.set_font("Arial", "", 10)
            pdf.ln(2)
            
            num_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if not num_cols:
                pdf.set_font("Arial", "I", 10)
                pdf.cell(0, 6, "No quantitative numeric features detected to calculate metrics.", ln=1)
            else:
                target_cols = num_cols[:3]
                metric_w = 45
                col_w = 48
                
                # Header Format Design
                pdf.set_font("Arial", "B", 9)
                pdf.set_fill_color(30, 58, 138)
                pdf.set_text_color(255, 255, 255)
                
                pdf.cell(metric_w, 7.5, " Measure", border=1, fill=True)
                for col in target_cols:
                    pdf.cell(col_w, 7.5, safe_txt(str(col)[:20]), border=1, fill=True, align="C")
                pdf.ln()

                # Table Metric Processing Loop
                stats = self.df.describe()
                pdf.set_font("Arial", "", 9.5)
                row_toggle = False
                
                for idx in ["count", "mean", "std", "min", "max"]:
                    if idx in stats.index:
                        pdf.set_fill_color(245, 247, 250) if row_toggle else pdf.set_fill_color(255, 255, 255)
                        pdf.set_text_color(31, 41, 55)
                        
                        pdf.cell(metric_w, 7, f" {idx.title()}", border=1, fill=True)
                        for col in target_cols:
                            val = stats.loc[idx, col]
                            val_str = f"{val:,.2f}" if not np.isnan(val) else "N/A"
                            pdf.cell(col_w, 7, safe_txt(val_str), border=1, fill=True, align="R")
                        pdf.ln()
                        row_toggle = not row_toggle

            #  SECTION 4: QUALITATIVE PATTERNS
            add_section_header("4. Category and Segment Patterns")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(55, 65, 81)
            
            cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
            clean_cat_cols = [c for c in cat_cols if c.lower() not in ['id', 'customer name', 'name', 'unnamed']]
            if not clean_cat_cols:
                clean_cat_cols = cat_cols[:3]

            if not cat_cols:
                profile_summary = (
                    "The dataset does not contain reliable category fields, so no "
                    "category-level comparison is included."
                )
            else:
                profile_summary = ""
                for c in clean_cat_cols[:3]:
                    if not self.df[c].empty:
                        top_node = self.df[c].mode()[0]
                        percentage = (self.df[c] == top_node).mean() * 100
                        profile_summary += (
                            f"In {c}, the most common value is {top_node}, representing "
                            f"{percentage:.2f} percent of the available records. This "
                            "concentration is worth comparing with revenue, profit, cost, "
                            "returns, or another relevant outcome before management makes "
                            "a segment-level decision.\n\n"
                        )
            
            pdf.multi_cell(0, 5.0, safe_txt(profile_summary.strip()))

            pdf.add_page()

            #  SECTION 5: STRATEGIC ROADMAP
            add_section_header("5. Recommended Actions")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(30, 41, 59)
            
            rec_topic = "Strategic Recommendations Action Plan Points"
            if self.revision_notes:
                rec_topic += f". Address admin revision feedback: {self.revision_notes}"
            rec_text = self._agent_section("RECOMMENDATIONS")
            if not rec_text:
                rec_text = (
                    self.ai_agent._get_fallback_text("Recommendations", self.df)
                    if self.agent_narrative
                    else self.ai_agent.generate_report_text(self.df, rec_topic)
                )
            pdf.multi_cell(0, 5.0, safe_txt(rec_text), border=0)

            # SECTION 6: LIMITATIONS AND GOVERNANCE
            limitations_text = self._agent_section("LIMITATIONS")
            if limitations_text:
                add_section_header("6. Limitations and Human Review")
                pdf.set_font("Arial", "", 10)
                pdf.set_text_color(55, 65, 81)
                pdf.multi_cell(0, 5.0, safe_txt(limitations_text), border=0)

            add_section_header("7. Management Review Checklist")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(55, 65, 81)
            checklist = (
                "1. Confirm that the data period and business scope match the decision.\n"
                "2. Review the highest-risk unusual records with the responsible owner.\n"
                "3. Compare forecast values with actual results as new periods close.\n"
                "4. Record any rejected recommendation and the reason for rejection.\n"
                "5. Approve publication only after the evidence and actions are accepted."
            )
            pdf.multi_cell(0, 6.0, checklist)
            pdf.ln(3)
            pdf.set_fill_color(255, 247, 214)
            pdf.set_text_color(92, 69, 0)
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(
                0,
                6.0,
                "Governance requirement: download and publication are permitted only "
                "after an authorized human reviewer approves this report in InsightHive.",
                fill=True,
            )

            # Final standard byte output extraction stream
            try:
                raw_bytes = pdf.output(dest='S')
                if isinstance(raw_bytes, str):
                    return bytes(raw_bytes.encode('latin-1', 'ignore'))
                return bytes(raw_bytes)
            except Exception:
                raw_bytes = pdf.output()
                if isinstance(raw_bytes, str):
                    return bytes(raw_bytes.encode('latin-1', 'ignore'))
                return bytes(raw_bytes)

        except Exception as e:
            return self._generate_fallback_pdf(str(e))

    def _generate_fallback_pdf(self, error: str = "") -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "System Compilation Critical Block!", ln=1)
        pdf.ln(5)
        clean_error = str(error).replace("\n", " ").replace("\r", " ")
        pdf.multi_cell(0, 5, f"Tracking Trace Constraint Details: {clean_error}")
        try:
            raw_bytes = pdf.output(dest='S')
            if isinstance(raw_bytes, str):
                return bytes(raw_bytes.encode('latin-1', 'ignore'))
            return bytes(raw_bytes)
        except Exception:
            raw_bytes = pdf.output()
            if isinstance(raw_bytes, str):
                return bytes(raw_bytes.encode('latin-1', 'ignore'))
            return bytes(raw_bytes)
