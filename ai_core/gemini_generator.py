import os
import re
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None


@dataclass
class GenerationResult:
    content: str
    model: str
    demo_mode: bool


class GeminiDocumentGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
        self.fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite").strip()
        self.max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
        self.demo_mode = os.getenv("DEMO_MODE", "false").strip().lower() == "true"
        self.client = None

        if not self.demo_mode and self.api_key and genai is not None:
            self.client = genai.Client(api_key=self.api_key)

    @staticmethod
    def _clean_response(text: str) -> str:
        text = (text or "").strip()
        text = re.sub(r"^```(?:text|markdown)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def _build_prompt(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
        jurisdiction: str,
        language: str,
    ) -> str:
        return f"""You are a legal-document drafting assistant.

Create a professional DRAFT of the requested legal document using only the information supplied below. Do not invent names, addresses, money amounts, dates, obligations, statutes, case citations, or jurisdiction-specific legal requirements that were not supplied.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

USER-SUPPLIED TERMS (semicolon-separated where applicable):
{terms}

EFFECTIVE DATE:
{effective_date}

JURISDICTION (if supplied):
{jurisdiction or 'Not specified'}

LANGUAGE:
{language}

Output requirements:
1. Start with a clear document title in uppercase.
2. Include an effective-date line.
3. Identify the parties and their roles.
4. Use numbered sections with descriptive headings.
5. Incorporate every user-supplied term without changing its meaning.
6. If a material fact is missing, write [TO BE COMPLETED] rather than inventing it.
7. Include practical signature blocks where appropriate.
8. End with a short DRAFT NOTICE stating that the document should be reviewed by a qualified legal professional before signing.
9. Return plain text/Markdown only; no JSON and no code fences.
10. Write in {language}.
"""

    def _demo_document(self, document_type, parties, terms, effective_date, jurisdiction, language):
        term_items = [item.strip() for item in terms.split(";") if item.strip()]
        lines = [
            document_type.upper(),
            "",
            f"Effective Date: {effective_date}",
            f"Jurisdiction: {jurisdiction or '[TO BE COMPLETED]'}",
            "",
            "1. PARTIES",
            parties,
            "",
            "2. PURPOSE",
            f"This draft sets out the principal terms of the {document_type.lower()} between the parties identified above.",
            "",
            "3. TERMS AND CONDITIONS",
        ]
        if term_items:
            for index, item in enumerate(term_items, 1):
                lines.append(f"3.{index} {item}")
        else:
            lines.append("3.1 [TO BE COMPLETED]")
        lines.extend([
            "",
            "4. GENERAL PROVISIONS",
            "The parties should complete any missing commercial, factual, and jurisdiction-specific information before signing.",
            "",
            "5. SIGNATURES",
            "Party 1: ______________________________    Date: ______________",
            "Party 2: ______________________________    Date: ______________",
            "",
            "DRAFT NOTICE",
            "This document is a drafting template for informational purposes and should be reviewed by a qualified legal professional before signing.",
        ])
        return "\n".join(lines)

    def generate_document(self, document_type, parties, terms, effective_date, jurisdiction="", language="English"):
        if self.demo_mode:
            return GenerationResult(
                content=self._demo_document(document_type, parties, terms, effective_date, jurisdiction, language),
                model="demo-mode",
                demo_mode=True,
            )

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to .env, or set DEMO_MODE=true for local testing."
            )
        if genai is None:
            raise RuntimeError("google-genai is not installed. Run: pip install -r requirements.txt")
        if self.client is None:
            self.client = genai.Client(api_key=self.api_key)

        prompt = self._build_prompt(
            document_type, parties, terms, effective_date, jurisdiction, language
        )
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_error = None
        for model_name in models_to_try:
            for attempt in range(self.max_retries + 1):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    content = self._clean_response(getattr(response, "text", ""))
                    if not content:
                        raise RuntimeError("Gemini returned an empty response.")
                    return GenerationResult(content=content, model=model_name, demo_mode=False)
                except Exception as exc:
                    last_error = exc
                    error_text = str(exc).upper()
                    transient = any(code in error_text for code in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500"))
                    if not transient:
                        raise
                    if attempt < self.max_retries:
                        time.sleep(3 * (2 ** attempt))

        raise RuntimeError(
            f"Gemini service is temporarily unavailable after retries. "
            f"Tried: {', '.join(models_to_try)}. Last error: {last_error}"
        )
