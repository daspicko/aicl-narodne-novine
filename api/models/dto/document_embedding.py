"""
document_embedding.py
---------------------
Pydantic DTOs for the DocumentEmbedding entity.

Embedding vectors are exposed as list[float] for JSON serialisation.
They are omitted from list / search responses to keep payloads small.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentEmbeddingBase(BaseModel):
    embedding_type: str       = Field(..., description=(
        "One of: 'document', 'title', 'summary_short', 'summary_detailed', "
        "'summary_structured_sto_zakon_ureduje', "
        "'summary_structured_na_koga_se_odnosi', "
        "'summary_structured_sto_uvodi_ili_mijenja', 'segment'"
    ))
    model_name:    str        = Field(..., description="HuggingFace model identifier")
    embedding_dim: int        = Field(384, description="Dimensionality of the vector")
    embedding:     list[float] = Field(..., description="Dense embedding vector")


class DocumentEmbeddingCreate(DocumentEmbeddingBase):
    document_id: int
    segment_id:  Optional[int] = None


class DocumentEmbeddingResponse(DocumentEmbeddingBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    document_id: int
    segment_id:  Optional[int] = None


class DocumentEmbeddingMeta(BaseModel):
    """Lightweight response that omits the vector — for listing purposes."""
    model_config = ConfigDict(from_attributes=True)

    id:             int
    document_id:    int
    segment_id:     Optional[int] = None
    embedding_type: str
    model_name:     str
    embedding_dim:  int
