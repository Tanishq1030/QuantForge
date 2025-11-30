# backend/db/schemas.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class VectorDocument(BaseModel):
    """Document to be vectorized and stored"""
    content: str = Field(..., description="Text content to vectorize")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")
    source: str = Field(..., description="Source identifier (e.g., 'news', 'social')")
    ticker: Optional[str] = Field(None, description="Associated ticker symbol")
    category: Optional[str] = Field(None, description="Category (e.g., 'earnings')")
    timestamp: Optional[datetime] = Field(None, description="Document timestamp")


class VectorIngestRequest(BaseModel):
    """Request for vector ingestion"""
    documents: List[VectorDocument] = Field(..., description="List of documents to ingest")
    collection_name: str = Field(default="FinancialInsight", description="Weaviate class/collection name")
    upsert: bool = Field(default=True, description="If True, update existing documents; if False, fail on duplicates")


class VectorIngestResponse(BaseModel):
    """Response from vector ingestion"""
    success: bool
    ingested_count: int
    updated_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)


class VectorSearchRequest(BaseModel):
    """Request for semantic search"""
    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Max results to return")
    collection_name: str = Field(default="FinancialInsight")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions (ticker, category, date range)")
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence threshold")


class VectorSearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    distance: float = Field(..., description="Vector distance (lower = more similar)")
    confidence: float = Field(..., description="Confidence score (0-1)")


class VectorSearchResponse(BaseModel):
    success: bool
    query: str
    results: List[VectorSearchResult]
    total_results: int
    execution_time_ms: float
