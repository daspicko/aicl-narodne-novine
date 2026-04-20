"""
search.py
---------
Pydantic DTOs for search request / response.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SearchType(str, Enum):
    lexical  = "lexical"
    semantic = "semantic"
    hybrid   = "hybrid"


class SearchRequest(BaseModel):
    query:       str         = Field(..., min_length=1, description="Search query text")
    search_type: SearchType  = Field(SearchType.hybrid, description="Search strategy")
    vrsta:       Optional[str] = Field(None, description="Filter by document type (Zakon, Uredba …)")
    izdanje:     Optional[str] = Field(None, description="Filter by NN issue (e.g. 'NN 10/1990')")
    page:        int         = Field(1,  ge=1,  description="Page number (1-based)")
    page_size:   int         = Field(10, ge=1, le=100, description="Results per page")


class SearchResultItem(BaseModel):
    """One document card in a search result list."""
    id:               int
    eli:              str
    vrsta:            Optional[str]
    izdanje:          Optional[str]
    donositelj:       Optional[str]
    datum:            Optional[str]
    naslov:           str
    short_summary:    Optional[str] = None
    match_score:      Optional[float] = Field(None, description="Relevance score [0–1]")
    match_type:       Optional[str]   = Field(None, description="'lexical', 'semantic', or 'hybrid'")
    highlights:       list[str]       = Field(default_factory=list,
                                              description="Matching text snippets")
    key_info_preview: Optional[dict]  = Field(None,
                                              description="subjects + deadlines preview")


class SearchResponse(BaseModel):
    query:      str
    search_type: SearchType
    page:       int
    page_size:  int
    total:      int
    results:    list[SearchResultItem]
