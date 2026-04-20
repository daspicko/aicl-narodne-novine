from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from api.database import Base


class DocumentSummary(Base):
    """
    One summary entry per (document, summary_type).

    summary_type values
    -------------------
    'short'                               – 3 extractive sentences
    'detailed'                            – 8 extractive sentences
    'structured_sto_zakon_ureduje'
    'structured_na_koga_se_odnosi'
    'structured_sto_uvodi_ili_mijenja'
    """
    __tablename__ = "document_summaries"

    document_id  = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    summary_type = Column(String(64),  nullable=False)
    text         = Column(Text,        nullable=False)
    model_name   = Column(String(128), nullable=True)

    document = relationship("Document", back_populates="summaries")

    __table_args__ = (
        UniqueConstraint("document_id", "summary_type", name="uq_summary_type"),
    )

    def __repr__(self) -> str:
        return f"<DocumentSummary id={self.id} type={self.summary_type!r}>"
