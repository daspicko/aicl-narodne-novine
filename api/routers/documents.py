"""
routers/documents.py
--------------------
CRUD endpoints for documents and their sub-resources.

GET    /api/documents                   – paginated list
POST   /api/documents                   – create
GET    /api/documents/{id}              – detail by PK
PUT    /api/documents/{id}              – full replace
PATCH  /api/documents/{id}              – partial update
DELETE /api/documents/{id}              – delete

GET    /api/documents/eli/{eli}         – detail by ELI (URL-encoded)

GET    /api/documents/{id}/segments     – list segments
GET    /api/documents/{id}/summaries    – list summaries
GET    /api/documents/{id}/key-information
"""

from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.crud import documents as crud
from api.database import get_db
from api.models.dto import (
    DocumentCreate,
    DocumentKeyInformationResponse,
    DocumentListItem,
    DocumentResponse,
    DocumentSegmentResponse,
    DocumentSummaryResponse,
    DocumentUpdate,
    PaginatedResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_or_404(document_id: int, db: Session):
    doc = crud.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Document {document_id} not found")
    return doc


# ---------------------------------------------------------------------------
# List & create
# ---------------------------------------------------------------------------

@router.get("", response_model=PaginatedResponse[DocumentListItem], summary="List documents")
def list_documents(
    page:      int          = Query(1,  ge=1),
    page_size: int          = Query(20, ge=1, le=100),
    vrsta:     str | None   = Query(None, description="Filter by document type"),
    izdanje:   str | None   = Query(None, description="Filter by NN issue"),
    db: Session = Depends(get_db),
):
    items, total = crud.list_documents(db, page=page, page_size=page_size,
                                       vrsta=vrsta, izdanje=izdanje)
    list_items = [_to_list_item(d) for d in items]
    return PaginatedResponse.create(items=list_items, total=total,
                                    page=page, page_size=page_size)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED,
             summary="Create document")
def create_document(data: DocumentCreate, db: Session = Depends(get_db)):
    return crud.create_document(db, data)


# ---------------------------------------------------------------------------
# By ELI  (must come before /{id} to avoid routing collision)
# ---------------------------------------------------------------------------

@router.get("/eli/{eli:path}", response_model=DocumentResponse, summary="Get document by ELI")
def get_by_eli(eli: str, db: Session = Depends(get_db)):
    doc = crud.get_document_by_eli(db, unquote(eli))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Document with ELI '{eli}' not found")
    return doc


# ---------------------------------------------------------------------------
# By ID
# ---------------------------------------------------------------------------

@router.get("/{document_id}", response_model=DocumentResponse, summary="Get document by ID")
def get_document(document_id: int, db: Session = Depends(get_db)):
    return _doc_or_404(document_id, db)


@router.put("/{document_id}", response_model=DocumentResponse, summary="Replace document")
def replace_document(document_id: int, data: DocumentCreate, db: Session = Depends(get_db)):
    _doc_or_404(document_id, db)
    update_data = DocumentUpdate(**data.model_dump())
    return crud.update_document(db, document_id, update_data)


@router.patch("/{document_id}", response_model=DocumentResponse, summary="Partial update")
def patch_document(document_id: int, data: DocumentUpdate, db: Session = Depends(get_db)):
    doc = crud.update_document(db, document_id, data)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Document {document_id} not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete document")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    if not crud.delete_document(db, document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Document {document_id} not found")


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------

@router.get("/{document_id}/segments",
            response_model=list[DocumentSegmentResponse],
            summary="List segments (članci) for a document")
def get_segments(document_id: int, db: Session = Depends(get_db)):
    _doc_or_404(document_id, db)
    return crud.list_segments(db, document_id)


@router.get("/{document_id}/summaries",
            response_model=list[DocumentSummaryResponse],
            summary="List summaries for a document")
def get_summaries(document_id: int, db: Session = Depends(get_db)):
    _doc_or_404(document_id, db)
    return crud.list_summaries(db, document_id)


@router.get("/{document_id}/key-information",
            response_model=DocumentKeyInformationResponse,
            summary="Get extracted key information for a document")
def get_key_information(document_id: int, db: Session = Depends(get_db)):
    _doc_or_404(document_id, db)
    ki = crud.get_key_information(db, document_id)
    if not ki:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Key information not available for this document")
    return ki


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _to_list_item(doc) -> DocumentListItem:
    short = next(
        (s.text for s in (doc.summaries or []) if s.summary_type == "short"),
        None,
    )
    return DocumentListItem(
        id=doc.id,
        eli=doc.eli,
        vrsta=doc.vrsta,
        izdanje=doc.izdanje,
        donositelj=doc.donositelj,
        datum=doc.datum,
        publication_date=doc.publication_date,
        naslov=doc.naslov,
        short_summary=short,
    )
