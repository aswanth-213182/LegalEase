from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_core.gemini_generator import GeminiDocumentGenerator

router = APIRouter()
generator = GeminiDocumentGenerator()


class DocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=2, max_length=120)
    parties: str = Field(..., min_length=2, max_length=5000)
    terms: str = Field(..., min_length=2, max_length=10000)
    effective_date: str = Field(..., min_length=2, max_length=100)
    jurisdiction: Optional[str] = Field(default="", max_length=200)
    language: str = Field(default="English", min_length=2, max_length=50)


class DocumentResponse(BaseModel):
    success: bool
    document_type: str
    content: str
    model: str
    demo_mode: bool


@router.post("/generate", response_model=DocumentResponse)
def generate_document(request: DocumentRequest):
    try:
        result = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
            jurisdiction=request.jurisdiction,
            language=request.language,
        )
        return DocumentResponse(
            success=True,
            document_type=request.document_type,
            content=result.content,
            model=result.model,
            demo_mode=result.demo_mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
