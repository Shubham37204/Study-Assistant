from __future__ import annotations
from pydantic import Field
from schemas.ingestion import StrictBaseModel  

class Chunk(StrictBaseModel):
    chunk_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    chunk_index: int = Field(..., ge=0)
    total_chunks: int | None = Field(default=None, ge=1)
    metadata: dict[str, str] = Field(default_factory=dict)
    