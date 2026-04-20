from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy.orm import relationship

from api.database import Base


class DocumentKeyInformation(Base):
    """
    Extracted key information for one document (one row per document).

    All extracted fields are stored as PostgreSQL TEXT[] arrays so individual
    items remain queryable without JSON parsing.

    Fields
    ------
    responsible_bodies  – ministries, courts, agencies mentioned in the law
    obligations         – sentences describing duties ("dužan je", "mora" …)
    deadlines           – temporal expressions ("u roku od 30 dana" …)
    scope               – sentences defining applicability
    subjects            – thematic topics derived from title / headings
    sanctions           – penalty / prohibition clauses
    """
    __tablename__ = "document_key_information"

    document_id = Column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )

    responsible_bodies = Column(ARRAY(TEXT), nullable=False, server_default="{}")
    obligations        = Column(ARRAY(TEXT), nullable=False, server_default="{}")
    deadlines          = Column(ARRAY(TEXT), nullable=False, server_default="{}")
    scope              = Column(ARRAY(TEXT), nullable=False, server_default="{}")
    subjects           = Column(ARRAY(TEXT), nullable=False, server_default="{}")
    sanctions          = Column(ARRAY(TEXT), nullable=False, server_default="{}")

    document = relationship("Document", back_populates="key_information")

    def __repr__(self) -> str:
        return f"<DocumentKeyInformation id={self.id} document_id={self.document_id}>"
