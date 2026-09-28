# LegalEase — AI-Powered Legal Document Generator

LegalEase is a FastAPI + Streamlit application that generates structured legal-document drafts with Google Gemini, provides an editable preview, and exports the edited document as TXT, DOCX, or PDF.

## Features

- Employment contracts, NDAs, lease agreements, service agreements, offer letters, and custom legal documents.
- Gemini-powered drafting with configurable model through `GEMINI_MODEL`.
- FastAPI `POST /generate` API.
- Streamlit frontend with editable document preview.
- DOCX with logo, title, headings, terms table, and footer.
- PDF with logo/header/footer and clean section formatting.
- TXT export.
- Demo mode for local UI/API testing without an API key.
- Input validation, error handling, and a health endpoint.

## Important

LegalEase generates drafts for informational and drafting assistance. It is not a substitute for a qualified lawyer and does not guarantee legal validity in a particular jurisdiction.


## Gemini 503 handling
The app retries transient Gemini 503/429/500 errors with exponential backoff and then tries `GEMINI_FALLBACK_MODEL`. If Google is temporarily overloaded, you can also change `GEMINI_MODEL` in `.env` to a currently available stable model.
"# LegalEase" 
"# LegalEase" 
