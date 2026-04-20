"""
document_summary.py
-------------------
Pydantic DTOs for the DocumentSummary entity.

summary_type values
-------------------
'short'                               – 3 extractive sentences
'detailed'                            – 8 extractive sentences
'structured_sto_zakon_ureduje'
'structured_na_koga_se_odnosi'
'structured_sto_uvodi_ili_mijenja'
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentSummaryBase(BaseModel):
    summary_type: str           = Field(..., description="Summary type identifier")
    text:         str           = Field(..., description="Summary text")
    model_name:   Optional[str] = Field(None, description="Model used to generate this summary")


class DocumentSummaryCreate(DocumentSummaryBase):
    document_id: int


class DocumentSummaryResponse(DocumentSummaryBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    document_id: int


class StructuredSummaryResponse(BaseModel):
    """Convenience shape that groups the three structured summary fields."""
    sto_zakon_ureduje:        Optional[str] = None
    na_koga_se_odnosi:        Optional[str] = None
    sto_uvodi_ili_mijenja:    Optional[str] = None


class AllSummariesResponse(BaseModel):
    """All summaries for one document grouped by type."""
    short:      Optional[str]                     = None
    detailed:   Optional[str]                     = None
    structured: StructuredSummaryResponse         = Field(default_factory=StructuredSummaryResponse)
