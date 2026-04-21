"""
api/models/db
-------------
SQLAlchemy ORM models for the Croatian legal document processing.

Import any model directly from this package:

    from api.models.db import Document, DocumentSegment
    from api.models.db import DocumentSummary, DocumentKeyInformation, DocumentEmbedding
"""

from api.models.db.document import Document
from api.models.db.document_segment import DocumentSegment
from api.models.db.document_summary import DocumentSummary
from api.models.db.document_key_information import DocumentKeyInformation
from api.models.db.document_embedding import DocumentEmbedding

__all__ = [
    "Document",
    "DocumentSegment",
    "DocumentSummary",
    "DocumentKeyInformation",
    "DocumentEmbedding",
]
