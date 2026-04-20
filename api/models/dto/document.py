"""
document.py
-----------
Pydantic DTOs for the Document entity.

Shapes
------
DocumentBase        – shared writable fields
DocumentCreate      – POST body (create)
DocumentUpdate      – PATCH body (partial update)
DocumentResponse    – full document detail response (includes nested relations)
DocumentListItem    – compact card for list / search results
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from api.models.dto.document_summary import DocumentSummaryResponse
from api.models.dto.document_key_information import DocumentKeyInformationResponse
from api.models.dto.document_segment import DocumentSegmentResponse


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class DocumentBase(BaseModel):
    eli:              str          = Field(..., description="European Legislation Identifier")
    eli_url:          Optional[str] = None
    broj_dokumenta:   Optional[str] = None

    dio:              Optional[str] = Field(None, description="'Službeni', 'Oglasni' …")
    vrsta:            Optional[str] = Field(None, description="'Zakon', 'Uredba', 'Odluka' …")
    izdanje:          Optional[str] = Field(None, examples=["NN 10/1990"])
    izdanje_url:      Optional[str] = None

    donositelj:       Optional[str] = Field(None, description="Issuing body (raw string)")
    datum:            Optional[str] = Field(None, description="Original date string, e.g. '13.2.1990.'")
    publication_date: Optional[datetime] = None

    naslov:     str           = Field(..., description="Document title")
    opis:       Optional[str] = Field(None, description="Preamble text")
    doc_cleaned: Optional[str] = Field(None, description="Full cleaned plain text")


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    """All fields optional for PATCH semantics."""
    eli:              Optional[str]      = None
    eli_url:          Optional[str]      = None
    broj_dokumenta:   Optional[str]      = None
    dio:              Optional[str]      = None
    vrsta:            Optional[str]      = None
    izdanje:          Optional[str]      = None
    izdanje_url:      Optional[str]      = None
    donositelj:       Optional[str]      = None
    datum:            Optional[str]      = None
    publication_date: Optional[datetime] = None
    naslov:           Optional[str]      = None
    opis:             Optional[str]      = None
    doc_cleaned:      Optional[str]      = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class DocumentResponse(DocumentBase):
    """Full document detail – includes all nested relations."""
    model_config = ConfigDict(from_attributes=True)

    id:         int
    created_at: datetime
    updated_at: datetime

    summaries:       list[DocumentSummaryResponse]          = []
    key_information: Optional[DocumentKeyInformationResponse] = None
    segments:        list[DocumentSegmentResponse]          = []


class DocumentListItem(BaseModel):
    """Compact representation used in list and search result cards."""
    model_config = ConfigDict(from_attributes=True)

    id:               int
    eli:              str
    vrsta:            Optional[str]
    izdanje:          Optional[str]
    donositelj:       Optional[str]
    datum:            Optional[str]
    publication_date: Optional[datetime]
    naslov:           str

    # Populated from DocumentSummary if available
    short_summary:    Optional[str] = None
