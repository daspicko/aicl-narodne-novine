"""
routers/admin.py
----------------
Admin-only endpoints protected by x-api-key.

DELETE /api/admin/db/purge  – truncate all tables (cascade)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies.auth import require_api_key

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_api_key)])

# Tables in dependency order – children first so FK constraints are satisfied
# even without CASCADE (safety net for non-PG engines).
_TABLES = [
    "document_embeddings",
    "document_key_information",
    "document_summaries",
    "document_segments",
    "documents",
]


@router.delete(
    "/db/purge",
    status_code=status.HTTP_200_OK,
    summary="Purge all data from the database",
    description=(
        "Truncates every table in cascade order. "
        "**Irreversible** – use only in development / testing. "
        "Requires a valid `x-api-key` header."
    ),
)
def purge_database(db: Session = Depends(get_db)):
    # TRUNCATE … RESTART IDENTITY CASCADE is the cleanest single statement on PostgreSQL
    table_list = ", ".join(_TABLES)
    db.execute(text(f"TRUNCATE {table_list} RESTART IDENTITY CASCADE"))
    db.commit()
    return {"purged": _TABLES, "status": "ok"}
