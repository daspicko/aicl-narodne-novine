"""
crud/documents.py
-----------------
All database operations for the Document entity and its relations.
"""

from __future__ import annotations

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload

from api.models.db import (
    Document,
    DocumentSegment,
    DocumentSummary,
    DocumentKeyInformation,
    DocumentEmbedding,
)
from api.models.dto import (
    DocumentCreate,
    DocumentUpdate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_query(db: Session):
    """Eager-load all relations in a single query."""
    return (
        db.query(Document)
        .options(
            selectinload(Document.summaries),
            selectinload(Document.key_information),
            selectinload(Document.segments),
        )
    )


# ---------------------------------------------------------------------------
# Documents – read
# ---------------------------------------------------------------------------

def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return _base_query(db).filter(Document.id == document_id).first()


def get_document_by_eli(db: Session, eli: str) -> Document | None:
    return _base_query(db).filter(Document.eli == eli).first()


def list_documents(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    vrsta: str | None = None,
    izdanje: str | None = None,
) -> tuple[list[Document], int]:
    """Return (items, total) with optional filters."""
    q = db.query(Document)
    if vrsta:
        q = q.filter(Document.vrsta.ilike(f"%{vrsta}%"))
    if izdanje:
        q = q.filter(Document.izdanje.ilike(f"%{izdanje}%"))

    total = q.with_entities(func.count(Document.id)).scalar()
    items = (
        q.order_by(Document.datum.desc(), Document.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


# ---------------------------------------------------------------------------
# Documents – write
# ---------------------------------------------------------------------------

def create_document(db: Session, data: DocumentCreate) -> Document:
    doc = Document(**data.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document(db: Session, document_id: int, data: DocumentUpdate) -> Document | None:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, document_id: int) -> bool:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------

def list_segments(db: Session, document_id: int) -> list[DocumentSegment]:
    return (
        db.query(DocumentSegment)
        .filter(DocumentSegment.document_id == document_id)
        .order_by(DocumentSegment.segment_order)
        .all()
    )


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------

def list_summaries(db: Session, document_id: int) -> list[DocumentSummary]:
    return (
        db.query(DocumentSummary)
        .filter(DocumentSummary.document_id == document_id)
        .all()
    )


def upsert_summary(
    db: Session,
    document_id: int,
    summary_type: str,
    text: str,
    model_name: str | None = None,
) -> DocumentSummary:
    existing = (
        db.query(DocumentSummary)
        .filter(
            DocumentSummary.document_id == document_id,
            DocumentSummary.summary_type == summary_type,
        )
        .first()
    )
    if existing:
        existing.text = text
        if model_name:
            existing.model_name = model_name
        db.commit()
        db.refresh(existing)
        return existing

    summary = DocumentSummary(
        document_id=document_id,
        summary_type=summary_type,
        text=text,
        model_name=model_name,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


# ---------------------------------------------------------------------------
# Key information
# ---------------------------------------------------------------------------

def get_key_information(db: Session, document_id: int) -> DocumentKeyInformation | None:
    return (
        db.query(DocumentKeyInformation)
        .filter(DocumentKeyInformation.document_id == document_id)
        .first()
    )


def upsert_key_information(
    db: Session,
    document_id: int,
    **fields,
) -> DocumentKeyInformation:
    existing = get_key_information(db, document_id)
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    ki = DocumentKeyInformation(document_id=document_id, **fields)
    db.add(ki)
    db.commit()
    db.refresh(ki)
    return ki


# ---------------------------------------------------------------------------
# Lexical search (full-text ILIKE)
# ---------------------------------------------------------------------------

def lexical_search(
    db: Session,
    query: str,
    page: int = 1,
    page_size: int = 10,
    vrsta: str | None = None,
) -> tuple[list[Document], int]:
    """Simple ILIKE search across naslov + doc_cleaned."""
    pattern = f"%{query}%"
    q = db.query(Document).filter(
        or_(
            Document.naslov.ilike(pattern),
            Document.doc_cleaned.ilike(pattern),
        )
    )
    if vrsta:
        q = q.filter(Document.vrsta.ilike(f"%{vrsta}%"))

    total = q.with_entities(func.count(Document.id)).scalar()
    items = (
        q.order_by(Document.datum.desc(), Document.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
