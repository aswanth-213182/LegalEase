import os
from datetime import date

import requests
import streamlit as st
from dotenv import load_dotenv

from formatters.docx_formatter import format_docx
from formatters.pdf_formatter import format_pdf
from formatters.utils import format_html_preview, sanitize_text

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "LegalEase")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title=APP_NAME, page_icon="⚖️", layout="wide")

st.markdown("""
<style>
.main-title {text-align:center; font-size:2.3rem; font-weight:800; margin-bottom:0.2rem;}
.subtitle {text-align:center; color:#6b7280; margin-bottom:1.2rem;}
.document-preview {background:#111827; color:#f9fafb; padding:28px; border-radius:14px; line-height:1.75; min-height:500px; max-height:700px; overflow:auto; font-family:Georgia, serif;}
.notice {padding:12px 16px; border-radius:10px; background:#fff7ed; border:1px solid #fed7aa; color:#7c2d12;}
</style>
""", unsafe_allow_html=True)

logo_path = os.path.join(os.path.dirname(__file__), "assets", "legal_ease_logo.png")
left, center, right = st.columns([1, 2, 1])
with center:
    if os.path.exists(logo_path):
        st.image(logo_path, width=105)
    st.markdown(f'<div class="main-title">{APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI-Powered Legal Document Generator</div>', unsafe_allow_html=True)

st.markdown('<div class="notice">LegalEase creates drafts for informational and drafting assistance. Review important documents with a qualified legal professional before signing.</div>', unsafe_allow_html=True)

if "document_text" not in st.session_state:
    st.session_state.document_text = ""
if "document_type" not in st.session_state:
    st.session_state.document_type = ""
if "model" not in st.session_state:
    st.session_state.model = ""

with st.form("document_form"):
    st.subheader("1. Document details")
    c1, c2 = st.columns(2)
    with c1:
        document_type = st.text_input(
            "Document Type *",
            placeholder="e.g. Freelance Work Contract, NDA, Lease Agreement",
        )
        effective_date = st.date_input("Effective Date *", value=date.today())
        language = st.selectbox("Language", ["English", "Tamil", "Hindi", "Malayalam", "Telugu", "Kannada"])
    with c2:
        jurisdiction = st.text_input("Jurisdiction (optional)", placeholder="e.g. Tamil Nadu, India")
        parties = st.text_area(
            "Parties Involved *",
            height=135,
            placeholder="Jane Doe (Service Provider), TechNova Inc. (Client)",
        )

    terms = st.text_area(
        "Terms & Conditions *",
        height=150,
        placeholder="Payment within 30 days of invoice; Confidentiality must be maintained; Either party may terminate with 15 days notice",
        help="Use semicolons to separate important terms.",
    )

    submitted = st.form_submit_button("Generate Document", type="primary", use_container_width=True)

if submitted:
    if not document_type.strip() or not parties.strip() or not terms.strip():
        st.error("Please complete Document Type, Parties Involved, and Terms & Conditions.")
    else:
        payload = {
            "document_type": document_type.strip(),
            "parties": parties.strip(),
            "terms": terms.strip(),
            "effective_date": effective_date.isoformat(),
            "jurisdiction": jurisdiction.strip(),
            "language": language,
        }
        with st.spinner("Generating your legal document..."):
            try:
                response = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=180)
                if response.ok:
                    data = response.json()
                    st.session_state.document_text = data["content"]
                    st.session_state.document_type = document_type.strip()
                    st.session_state.model = data.get("model", "")
                    st.success("Document generated successfully.")
                    if data.get("demo_mode"):
                        st.info("Demo mode is active. Set DEMO_MODE=false and add GEMINI_API_KEY in .env for real Gemini generation.")
                else:
                    try:
                        detail = response.json().get("detail", response.text)
                    except Exception:
                        detail = response.text
                    st.error(f"Backend error: {detail}")
            except requests.RequestException as exc:
                st.error(f"Could not connect to FastAPI at {BACKEND_URL}. Start the backend first. Details: {exc}")

if st.session_state.document_text:
    st.divider()
    st.subheader("2. Preview & Edit")
    if st.session_state.model:
        st.caption(f"Generation engine: {st.session_state.model}")

    edited = st.text_area(
        "Editable Document",
        value=st.session_state.document_text,
        height=560,
        key="editable_document",
    )
    st.session_state.document_text = edited

    st.markdown("**Styled Preview**")
    st.markdown(format_html_preview(st.session_state.document_text), unsafe_allow_html=True)

    st.subheader("3. Download")
    safe_type = "".join(ch if ch.isalnum() else "_" for ch in st.session_state.document_type.lower()).strip("_") or "legal_document"
    txt_bytes = sanitize_text(st.session_state.document_text).encode("utf-8")
    docx_bytes = format_docx(st.session_state.document_text, st.session_state.document_type, terms)
    pdf_bytes = format_pdf(st.session_state.document_text, st.session_state.document_type)

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("Download TXT", txt_bytes, file_name=f"{safe_type}.txt", mime="text/plain", use_container_width=True)
    with d2:
        st.download_button("Download DOCX", docx_bytes, file_name=f"{safe_type}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with d3:
        st.download_button("Download PDF", pdf_bytes, file_name=f"{safe_type}.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.caption("LegalEase • AI-assisted drafting • Review before signing")
