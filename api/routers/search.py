"""
routers/search.py
-----------------
Search endpoints.

POST  /api/search              – full hybrid / lexical / semantic search
GET   /api/search/suggest?q=   – lightweight title autocomplete
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.crud import documents as crud
from api.database import get_db
from api.models.dto import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchType,
)

router = APIRouter(prefix="/search", tags=["Search"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_to_result(doc, score: float | None = None, match_type: str = "lexical") -> SearchResultItem:
    short = next(
        (s.text for s in (doc.summaries or []) if s.summary_type == "short"),
        None,
    )
    ki = doc.key_information
    key_info_preview = None
    if ki:
        key_info_preview = {
            "subjects":  (ki.subjects or [])[:3],
            "deadlines": (ki.deadlines or [])[:2],
        }

    return SearchResultItem(
        id=doc.id,
        eli=doc.eli,
        match_score=score,
        match_type=match_type,
    )


# ---------------------------------------------------------------------------
# POST /api/search
# ---------------------------------------------------------------------------

@router.post("", response_model=SearchResponse, summary="Search documents")
def search(body: SearchRequest, db: Session = Depends(get_db)):
    """
    Hybrid search endpoint.

    Currently implements lexical (ILIKE) search.
    Semantic and hybrid modes fall back to lexical until pgvector
    similarity search is wired in.
    """
    docs, total = crud.lexical_search(
        db,
        query=body.query,
        page=body.page,
        page_size=body.page_size,
        vrsta=body.vrsta,
    )

    results = [_doc_to_result(d, match_type=body.search_type.value) for d in docs]

    return SearchResponse(
        query=body.query,
        search_type=body.search_type,
        page=body.page,
        page_size=body.page_size,
        total=total,
        results=results,
    )


# ---------------------------------------------------------------------------
# GET /api/search/suggest
# ---------------------------------------------------------------------------

@router.get("/suggest", summary="Title autocomplete suggestions")
def suggest(
    q: str     = Query(..., min_length=1, description="Partial title query"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Returns a list of { id, eli, naslov } objects whose title contains *q*.
    Intended for search-box autocomplete.
    """
    from api.models.db import Document
    from sqlalchemy import func

    rows = (
        db.query(Document.id, Document.eli, Document.naslov)
        .filter(Document.naslov.ilike(f"%{q}%"))
        .order_by(Document.datum.desc())
        .limit(limit)
        .all()
    )
    return [{"id": r.id, "eli": r.eli, "naslov": r.naslov} for r in rows]
