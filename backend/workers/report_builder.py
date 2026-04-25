"""
NEXUS Report Builder Worker — Compiles data, text, and charts into PDF reports.
Uses fpdf2 for lightweight, dependency-free PDF generation.
"""
from __future__ import annotations
import io
import base64
import logging
import tempfile
import os
from fpdf import FPDF
from workers.base_worker import BaseWorker, WorkerResult
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL, ARTIFACTS_DIR

logger = logging.getLogger(__name__)

REPORT_CONTENT_PROMPT = """You are a report writer. Generate the TEXT CONTENT for a professional PDF report.

RULES:
1. Write in clean, structured prose — NOT markdown.
2. Use this structure:
   - TITLE (one line)
   - EXECUTIVE SUMMARY (2-3 sentences)
   - KEY METRICS (bullet points with numbers)
   - DETAILED FINDINGS (paragraphs)
   - RECOMMENDATIONS (bullet points)
3. Be data-driven — reference specific numbers from the provided context.
4. Be concise but insightful.
5. Output ONLY the report text content, nothing else."""


class ReportBuilder(BaseWorker):
    name = "ReportBuilder"

    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        # Gather all context from previous steps
        accumulated = context.get("accumulated_context", "")
        chart_base64 = context.get("chart_data")
        previous_data = context.get("previous_data")

        data_summary = ""
        if previous_data is not None:
            import pandas as pd
            if isinstance(previous_data, pd.DataFrame):
                data_summary = previous_data.to_string()[:2000]
            else:
                data_summary = str(previous_data)[:2000]

        # Generate report content via LLM
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0.3,
            max_tokens=4096,
        )

        user_content = (
            f"Instruction: {instruction}\n\n"
            f"Data summary:\n{data_summary}\n\n"
            f"Execution context:\n{accumulated}\n\n"
            f"Generate the report content."
        )

        messages = [
            SystemMessage(content=REPORT_CONTENT_PROMPT),
            HumanMessage(content=user_content),
        ]

        response = await llm.ainvoke(messages)
        report_text = response.content.strip()

        # Build PDF with fpdf2
        try:
            # Sanitize text for Latin-1 encoding (fpdf2 default)
            def safe_text(text: str) -> str:
                # Strip markdown formatting
                import re
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
                text = re.sub(r'\*(.+?)\*', r'\1', text)      # *italic*
                text = re.sub(r'__(.+?)__', r'\1', text)      # __bold__
                text = re.sub(r'_(.+?)_', r'\1', text)        # _italic_
                text = re.sub(r'`(.+?)`', r'\1', text)        # `code`
                text = re.sub(r'^#{1,6}\s+', '', text)        # # headers

                replacements = {
                    '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
                    '\u201c': '"', '\u201d': '"', '\u2022': '-', '\u2026': '...',
                    '\u00b7': '-', '\u2010': '-', '\u2011': '-',
                    '\u2032': "'", '\u2033': '"', '\u00a0': ' ',
                }
                for k, v in replacements.items():
                    text = text.replace(k, v)
                return text.encode('latin-1', errors='replace').decode('latin-1')

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            left_margin = pdf.l_margin

            # Title — use multi_cell so long titles wrap safely
            pdf.set_font("Helvetica", "B", 20)
            lines = report_text.split("\n")
            title = safe_text(lines[0])[:80] if lines else "Report"
            pdf.set_x(left_margin)
            pdf.multi_cell(0, 12, title, align="C")
            pdf.ln(5)

            # Separator line
            pdf.set_draw_color(79, 70, 229)
            pdf.set_line_width(0.5)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(10)

            # Date
            from datetime import datetime, timezone
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(128, 128, 128)
            pdf.set_x(left_margin)
            pdf.multi_cell(0, 8, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", align="R")
            pdf.ln(5)

            # Body content
            pdf.set_text_color(0, 0, 0)
            body = "\n".join(lines[1:]) if len(lines) > 1 else report_text

            for paragraph in body.split("\n"):
                paragraph = safe_text(paragraph.strip())
                if not paragraph:
                    pdf.ln(3)
                    continue

                # Always reset X position to left margin
                pdf.set_x(left_margin)

                # Section headers (ALL CAPS lines or short uppercase-heavy lines)
                if paragraph.isupper() and len(paragraph) < 60:
                    pdf.ln(5)
                    pdf.set_font("Helvetica", "B", 13)
                    pdf.set_text_color(79, 70, 229)
                    pdf.multi_cell(0, 10, paragraph)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(2)
                # Bullet points
                elif paragraph.startswith(("- ", "* ")):
                    pdf.set_font("Helvetica", "", 11)
                    bullet_text = paragraph.lstrip("-* ").strip()
                    pdf.multi_cell(0, 7, "  - " + bullet_text)
                # Numbered items
                elif len(paragraph) > 2 and paragraph[0].isdigit() and paragraph[1] in ".):" :
                    pdf.set_font("Helvetica", "", 11)
                    pdf.multi_cell(0, 7, "  " + paragraph)
                # Regular paragraphs
                else:
                    pdf.set_font("Helvetica", "", 11)
                    pdf.multi_cell(0, 7, paragraph)
                    pdf.ln(2)

            # Embed chart image if available
            if chart_base64:
                try:
                    pdf.add_page()
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.set_text_color(79, 70, 229)
                    pdf.cell(0, 10, "VISUALIZATION", ln=True)
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(5)

                    # Save chart to temp file
                    chart_bytes = base64.b64decode(chart_base64)
                    chart_path = os.path.join(tempfile.gettempdir(), "nexus_chart.png")
                    with open(chart_path, "wb") as f:
                        f.write(chart_bytes)

                    pdf.image(chart_path, x=15, w=180)
                    os.remove(chart_path)
                except Exception as e:
                    logger.warning(f"ReportBuilder: Failed to embed chart: {e}")

            # Save PDF
            os.makedirs(ARTIFACTS_DIR, exist_ok=True)
            pdf_path = os.path.join(ARTIFACTS_DIR, "report.pdf")
            pdf.output(pdf_path)

            # Also get base64 for download
            with open(pdf_path, "rb") as f:
                pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

            return WorkerResult(
                success=True,
                output=f"PDF report generated successfully ({len(lines)} content lines, chart: {'embedded' if chart_base64 else 'none'})",
                data=pdf_base64,
                artifacts=[{
                    "name": "report.pdf",
                    "type": "application/pdf",
                    "base64": pdf_base64,
                }],
            )

        except Exception as e:
            return WorkerResult(
                success=False,
                error=f"PDF generation failed: {str(e)}",
            )
