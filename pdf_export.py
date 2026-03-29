"""
pdf_export.py — PDF generation for FOIA/RTI Request Generator.

Uses ReportLab to generate professional PDF versions of request letters.
Font: Helvetica, Size: 11pt, Line spacing: 14pt, Page: A4, Margins: 72pt.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def generate_pdf(letter_text: str, request_id: str, output_path: str):
    """
    Generate a PDF document from the rendered letter text.

    Args:
        letter_text: The complete rendered letter text.
        request_id: The unique request ID (used in header).
        output_path: Full path where the PDF will be saved.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create PDF document with A4 page size and 72pt (1 inch) margins
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Header style for request ID
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceAfter=6,
    )

    # Body text style
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        spaceAfter=4,
    )

    # Build the PDF content
    story = []

    # Add request ID header
    story.append(Paragraph(f"<b>{request_id}</b>", header_style))
    story.append(Spacer(1, 0.2 * inch))

    # Split letter text into paragraphs and add each
    paragraphs = letter_text.split("\n")
    for para_text in paragraphs:
        clean_text = para_text.strip()
        if not clean_text:
            # Empty line → spacer
            story.append(Spacer(1, 0.15 * inch))
        else:
            # Escape XML special characters for ReportLab
            clean_text = (
                clean_text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            story.append(Paragraph(clean_text, body_style))

    # Build PDF
    doc.build(story)
