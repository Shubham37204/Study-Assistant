from __future__ import annotations
from typing import Literal
from pydantic import Field, model_validator
from schemas.ingestion import StrictBaseModel  

SearchType = Literal["hybrid", "vector_only", "bm25_only"]
RetrievalSource = Literal["vector", "bm25"]

class SearchQuery(StrictBaseModel):
    query_text: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    vector_fetch_k: int = Field(default=20, ge=5, le=100)
    search_type: SearchType = "hybrid"

    @model_validator(mode="after")
    def validate_fetch_size(self) -> SearchQuery:  
        if self.vector_fetch_k < self.top_k:
            raise ValueError("vector_fetch_k must be >= top_k")
        return self


class ChunkResult(StrictBaseModel):
    chunk_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    score: float
    retrieval_sources: list[RetrievalSource] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_retrieval_sources(self) -> ChunkResult:
        if not self.retrieval_sources:
            raise ValueError("retrieval_sources must contain at least one source")
        return self


class RetrievalResult(StrictBaseModel):
    query_text: str = Field(..., min_length=1)
    chunks: list[ChunkResult] = Field(default_factory=list)
    search_type_used: SearchType
    total_candidates_before_rerank: int = Field(..., ge=0)
    reranking_applied: bool
    