from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from api.database import Base


class DocumentSegment(Base):
    """
    One članak (article) extracted from doc_segmented.

    text = all točke joined into a single string.
    segment_order = zero-based position within the document.
    """
    __tablename__ = "document_segments"

    document_id   = Column(BigInteger,   ForeignKey("documents.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    segment_order = Column(SmallInteger, nullable=False)  # position in doc
    clanak_label  = Column(String(32),   nullable=True)   # "Član 1.", "Član 2." …
    text          = Column(Text,         nullable=False)   # joined točke

    document  = relationship("Document", back_populates="segments")
    embedding = relationship(
        "DocumentEmbedding",
        primaryjoin=(
            "and_(DocumentEmbedding.document_id == DocumentSegment.document_id,"
            " DocumentEmbedding.segment_id == DocumentSegment.id)"
        ),
        foreign_keys="[DocumentEmbedding.document_id, DocumentEmbedding.segment_id]",
        viewonly=True,
    )

    __table_args__ = (
        UniqueConstraint("document_id", "segment_order", name="uq_segment_order"),
    )

    def __repr__(self) -> str:
        return f"<DocumentSegment id={self.id} clanak={self.clanak_label!r}>"
