from __future__ import annotations

from typing import Literal
from pydantic import Field
from schemas.ingestion import StrictBaseModel

SearchType = Literal["hybrid", "vector_only", "bm25_only"]
IngestionStatus = Literal["success", "partial", "failed"]


class UploadResponse(StrictBaseModel):
    document_id: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    total_chunks: int = Field(..., ge=0)
    summary: str
    key_topics: list[str] = Field(default_factory=list)
    status: IngestionStatus
    errors: list[str] = Field(default_factory=list)


class ConversationMessage(StrictBaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class QueryRequest(StrictBaseModel):
    query_text: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field(..., min_length=1)
    document_ids: list[str] = Field(default_factory=list)
    search_type: SearchType = "hybrid"
    conversation_history: list[ConversationMessage] = Field(default_factory=list, max_length=10)


class CitationResponse(StrictBaseModel):
    chunk_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    excerpt: str = Field(..., min_length=1)


class QueryResponse(StrictBaseModel):
    answer: str
    citations: list[CitationResponse] = Field(default_factory=list)
    intent: str
    search_type_used: SearchType = "hybrid"


class ErrorResponse(StrictBaseModel):
    error: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)
    