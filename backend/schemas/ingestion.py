from __future__ import annotations
from datetime import datetime, timezone 
from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class FileType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    MARKDOWN = "markdown"
    URL = "url"
    UNKNOWN = "unknown"


class IngestionError(StrictBaseModel):
    stage: Literal["parse", "ocr", "chunk", "embed", "store", "unknown"] = "unknown"
    message: str = Field(..., min_length=1)
    code: str | None = Field(default=None, max_length=80)
    page_number: int | None = Field(default=None, ge=1)
    recoverable: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)  
    )


class ExtractedPage(StrictBaseModel):
    page_number: int = Field(..., ge=1)
    raw_text: str = ""
    is_scanned: bool = False

    @computed_field
    @property
    def word_count(self) -> int:
        return len(self.raw_text.split())


class ExtractedDocument(StrictBaseModel):
    source_path: str = Field(..., min_length=1)
    file_type: FileType = FileType.UNKNOWN
    pages: list[ExtractedPage] = Field(default_factory=list)
    title: str | None = Field(default=None, max_length=300)
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) 
    )

    @computed_field                      
    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @model_validator(mode="after")
    def validate_page_numbers_unique(self) -> ExtractedDocument:
        page_numbers = [p.page_number for p in self.pages]
        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError("page_number values must be unique")
        return self


class DocumentSummary(StrictBaseModel):
    short_summary: str = Field(..., min_length=1, max_length=200)
    key_topics: list[str] = Field(default_factory=list, max_length=10)
    estimated_difficulty: Literal["beginner", "intermediate", "advanced"]

    @field_validator("key_topics")
    @classmethod
    def validate_topics(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for topic in value:
            normalized = topic.strip()
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned


class IngestionResult(StrictBaseModel):
    document_id: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    total_chunks: int = Field(..., ge=0)
    summary: DocumentSummary
    status: Literal["success", "partial", "failed"]
    errors: list[IngestionError] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_consistency(self) -> IngestionResult:
        if self.status in {"partial", "failed"} and not self.errors:
            raise ValueError("partial or failed ingestion must include errors")
        if self.status == "success" and self.errors:
            raise ValueError("successful ingestion should not include errors")
        return self
    