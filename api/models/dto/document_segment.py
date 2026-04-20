"""
document_segment.py
-------------------
Pydantic DTOs for the DocumentSegment entity.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentSegmentBase(BaseModel):
    clanak_label:  Optional[str] = Field(None, description="Article label, e.g. 'Član 1.'")
    segment_order: int           = Field(..., description="Zero-based position within the document")
    text:          str           = Field(..., description="Full article text (all točke joined)")


class DocumentSegmentCreate(DocumentSegmentBase):
    document_id: int


class DocumentSegmentResponse(DocumentSegmentBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    document_id: int
