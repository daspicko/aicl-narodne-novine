"""
document_key_information.py
---------------------------
Pydantic DTOs for the DocumentKeyInformation entity.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DocumentKeyInformationBase(BaseModel):
    responsible_bodies: list[str] = Field(default_factory=list,
                                          description="Ministries, courts, agencies …")
    obligations:        list[str] = Field(default_factory=list,
                                          description="Duty / obligation statements")
    deadlines:          list[str] = Field(default_factory=list,
                                          description="Temporal expressions (rokovi)")
    scope:              list[str] = Field(default_factory=list,
                                          description="Applicability / scope sentences")
    subjects:           list[str] = Field(default_factory=list,
                                          description="Thematic topics of the document")
    sanctions:          list[str] = Field(default_factory=list,
                                          description="Penalty / prohibition clauses")


class DocumentKeyInformationCreate(DocumentKeyInformationBase):
    document_id: int


class DocumentKeyInformationResponse(DocumentKeyInformationBase):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    document_id: int
