from io import BytesIO
import os
import re
from fpdf import FPDF

from .utils import LOGO_PATH, sanitize_text, split_sections


class LegalEasePDF(FPDF):
    def __init__(self, doc_type: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.doc_type = sanitize_text(doc_type)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 22, 18)

    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(str(LOGO_PATH), x=92, y=8, w=26)
        self.set_y(37)
        self.set_font("Helvetica", "B", 8)
        self.cell(0, 5, self.doc_type.upper(), align="C")
        self.ln(7)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 5, f"LegalEase | Draft for review | Page {self.page_no()}", align="C")


def _write_wrapped(pdf, text, bold=False, size=10.5, spacing=4.5):
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.multi_cell(0, spacing, sanitize_text(text), align="L")


def format_pdf(text: str, doc_type: str) -> bytes:
    pdf = LegalEasePDF(doc_type)
    pdf.add_page()
    for heading, body in split_sections(text):
        _write_wrapped(pdf, heading, bold=True, size=11, spacing=5)
        pdf.ln(1)
        for line in body:
            if not line:
                pdf.ln(2)
                continue
            bullet = bool(re.match(r"^[-*]\s+", line))
            clean = re.sub(r"^[-*]\s+", "", line)
            if bullet:
                _write_wrapped(pdf, "- " + clean, size=10, spacing=4.7)
            else:
                _write_wrapped(pdf, clean, size=10, spacing=4.7)
            pdf.ln(1.5)
        pdf.ln(2)
    return bytes(pdf.output())
