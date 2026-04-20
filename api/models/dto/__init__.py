"""
api/models/dto
--------------
Pydantic DTO (Data Transfer Object) models exposed by the FastAPI application.

All shapes are importable directly from this package:

    from api.models.dto import (
        DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListItem,
        DocumentSegmentCreate, DocumentSegmentResponse,
        DocumentSummaryCreate, DocumentSummaryResponse,
        AllSummariesResponse, StructuredSummaryResponse,
        DocumentKeyInformationCreate, DocumentKeyInformationResponse,
        DocumentEmbeddingCreate, DocumentEmbeddingResponse, DocumentEmbeddingMeta,
        SearchRequest, SearchResponse, SearchResultItem, SearchType,
        PaginatedResponse,
    )
"""

from api.models.dto.document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListItem,
)
from api.models.dto.document_segment import (
    DocumentSegmentBase,
    DocumentSegmentCreate,
    DocumentSegmentResponse,
)
from api.models.dto.document_summary import (
    DocumentSummaryBase,
    DocumentSummaryCreate,
    DocumentSummaryResponse,
    StructuredSummaryResponse,
    AllSummariesResponse,
)
from api.models.dto.document_key_information import (
    DocumentKeyInformationBase,
    DocumentKeyInformationCreate,
    DocumentKeyInformationResponse,
)
from api.models.dto.document_embedding import (
    DocumentEmbeddingBase,
    DocumentEmbeddingCreate,
    DocumentEmbeddingResponse,
    DocumentEmbeddingMeta,
)
from api.models.dto.search import (
    SearchType,
    SearchRequest,
    SearchResultItem,
    SearchResponse,
)
from api.models.dto.pagination import PaginatedResponse

__all__ = [
    # Document
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListItem",
    # Segment
    "DocumentSegmentBase",
    "DocumentSegmentCreate",
    "DocumentSegmentResponse",
    # Summary
    "DocumentSummaryBase",
    "DocumentSummaryCreate",
    "DocumentSummaryResponse",
    "StructuredSummaryResponse",
    "AllSummariesResponse",
    # Key information
    "DocumentKeyInformationBase",
    "DocumentKeyInformationCreate",
    "DocumentKeyInformationResponse",
    # Embeddings
    "DocumentEmbeddingBase",
    "DocumentEmbeddingCreate",
    "DocumentEmbeddingResponse",
    "DocumentEmbeddingMeta",
    # Search
    "SearchType",
    "SearchRequest",
    "SearchResultItem",
    "SearchResponse",
    # Pagination
    "PaginatedResponse",
]
