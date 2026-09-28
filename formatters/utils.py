import html
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "legal_ease_logo.png"


def sanitize_text(text: str) -> str:
    replacements = {
        "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-",
        "•": "-", "…": "...", "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text).strip()


def split_sections(text: str):
    sections = []
    current_heading = None
    current_body = []
    for raw in sanitize_text(text).splitlines():
        line = raw.strip()
        if not line:
            if current_body:
                current_body.append("")
            continue
        if re.match(r"^(\d+(?:\.\d+)?[.)]?|[A-Z][A-Z\s&/-]{4,})\s+", line):
            if current_heading is not None:
                sections.append((current_heading, current_body))
            current_heading = line
            current_body = []
        else:
            current_body.append(line)
    if current_heading is not None:
        sections.append((current_heading, current_body))
    if not sections:
        sections = [("DOCUMENT", sanitize_text(text).splitlines())]
    return sections


def terms_from_text(text: str):
    terms = []
    for line in sanitize_text(text).splitlines():
        line = line.strip()
        if line.startswith("-"):
            line = line[1:].strip()
        if re.match(r"^\d+\.\d+\s+", line):
            line = re.sub(r"^\d+\.\d+\s+", "", line)
        if line and not re.match(r"^(\d+\.)?\s*(PARTIES|PURPOSE|TERMS AND CONDITIONS|GENERAL PROVISIONS|SIGNATURES|DRAFT NOTICE)$", line, re.I):
            if len(line) <= 350:
                terms.append(line)
    return terms[:30]


def format_html_preview(text: str) -> str:
    safe = html.escape(sanitize_text(text)).replace("\n", "<br>")
    return f'<div class="document-preview">{safe}</div>'
