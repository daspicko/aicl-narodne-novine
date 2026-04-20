from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.orm import relationship

from api.database import Base


class Document(Base):
    """
    Canonical record for one legal document (zakon, uredba, odluka …).

    Sourced from the top-level fields of the embedded JSON:
        dio, vrsta, izdanje, brojDokumenta, donositelj, datum, eli, eliUrl,
        naslov, opis, doc_cleaned
    """
    __tablename__ = "documents"

    # --- identity -----------------------------------------------------------
    eli            = Column(String(255), nullable=False, unique=True, index=True)
    eli_url        = Column(Text,        nullable=True)
    broj_dokumenta = Column(String(32),  nullable=True)

    # --- classification -----------------------------------------------------
    dio            = Column(String(64),  nullable=True)   # "Službeni", "Oglasni" …
    vrsta          = Column(String(64),  nullable=True)   # "Zakon", "Uredba" …
    izdanje        = Column(String(64),  nullable=True)   # "NN 10/1990"
    izdanje_url    = Column(Text,        nullable=True)

    # --- authorship / date --------------------------------------------------
    donositelj       = Column(Text,     nullable=True)    # issuing body (raw string)
    datum            = Column(String(32), nullable=True)  # original date string "13.2.1990."
    publication_date = Column(DateTime, nullable=True)    # parsed datetime (nullable)

    # --- content ------------------------------------------------------------
    naslov      = Column(Text, nullable=False)
    opis        = Column(Text, nullable=True)   # preamble
    doc_cleaned = Column(Text, nullable=True)   # full cleaned text

    # --- processing metadata ------------------------------------------------
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # --- relationships ------------------------------------------------------
    segments        = relationship("DocumentSegment",        back_populates="document",
                                   cascade="all, delete-orphan")
    summaries       = relationship("DocumentSummary",        back_populates="document",
                                   cascade="all, delete-orphan")
    key_information = relationship("DocumentKeyInformation", back_populates="document",
                                   uselist=False, cascade="all, delete-orphan")
    embeddings      = relationship("DocumentEmbedding",      back_populates="document",
                                   cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document id={self.id} eli={self.eli!r}>"
