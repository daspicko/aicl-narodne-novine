from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from api.database import Base


class DocumentEmbedding(Base):
    """
    pgvector embedding for one (document, embedding_type) combination.

    embedding_type values
    ---------------------
    'document'                                 – full doc_cleaned embedding
    'title'                                    – naslov embedding
    'summary_short'                            – short summary embedding
    'summary_detailed'                         – detailed summary embedding
    'summary_structured_sto_zakon_ureduje'
    'summary_structured_na_koga_se_odnosi'
    'summary_structured_sto_uvodi_ili_mijenja'
    'segment'                                  – individual članak embedding

    segment_id is set only for 'segment' type; NULL for all other types.
    """
    __tablename__ = "document_embeddings"

    document_id = Column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    segment_id = Column(
        BigInteger,
        ForeignKey("document_segments.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )

    embedding_type = Column(String(80),   nullable=False)
    model_name     = Column(String(128),  nullable=False)
    embedding_dim  = Column(SmallInteger, nullable=False, default=384)

    # pgvector column – 384 dimensions (sentence-transformers/all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=False)

    document = relationship("Document", back_populates="embeddings")
    segment  = relationship("DocumentSegment", foreign_keys=[segment_id])

    __table_args__ = (
        UniqueConstraint(
            "document_id", "segment_id", "embedding_type", "model_name",
            name="uq_embedding_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentEmbedding id={self.id} "
            f"type={self.embedding_type!r} doc={self.document_id}>"
        )
