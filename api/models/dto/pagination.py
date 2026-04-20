"""
pagination.py
-------------
Generic pagination envelope used across all list endpoints.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Wrap any list response with pagination metadata.

    Usage in a router::

        return PaginatedResponse[DocumentListItem](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
    """
    items:     list[T]
    total:     int  = Field(..., description="Total number of matching records")
    page:      int  = Field(..., description="Current page (1-based)")
    page_size: int  = Field(..., description="Items per page")
    pages:     int  = Field(..., description="Total number of pages")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)
