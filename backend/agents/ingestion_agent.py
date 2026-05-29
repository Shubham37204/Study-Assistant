from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from core.extractors.base_extractor import BaseExtractor
from core.extractors.image_extractor import ImageExtractor
from core.extractors.link_extractor import LinkExtractor
from core.extractors.pdf_extractor import PDFExtractor
from core.extractors.text_extractor import TextExtractor
from core.file_detector import FileDetector
from core.summarizer import DocumentSummarizer
from core.text_cleaner import TextCleaner
from db.repository import DocumentRepository
from providers.llm.base import BaseLLMProvider
from schemas.ingestion import (
    DocumentSummary,
    ExtractedDocument,
    FileType,
    IngestionError,
    IngestionResult,
)

logger = logging.getLogger(__name__)


class UnsupportedFileTypeError(Exception):
    def __init__(self, file_type: str, source: str | Path) -> None:
        self.file_type = file_type
        self.source = str(source)
        super().__init__(f"Unsupported file type '{file_type}' for source: {self.source}")


class IngestionAgent:
    def __init__(
        self,
        repository: DocumentRepository,
        llm: BaseLLMProvider,
        chunker: Any,
        embedder: Any,
        vector_store: Any,
        keyword_store: Any,
    ) -> None:
        self.detector = FileDetector()
        self.cleaner = TextCleaner()
        self.summarizer = DocumentSummarizer(llm=llm)
        self.repository = repository
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.keyword_store = keyword_store

        self._extractors: dict[FileType, BaseExtractor] = {
            FileType.PDF: PDFExtractor(),
            FileType.IMAGE: ImageExtractor(),
            FileType.URL: LinkExtractor(),
            FileType.TEXT: TextExtractor(),
            FileType.MARKDOWN: TextExtractor(),
        }

    def run(
        self,
        source: str | Path,
        user_id: str,
        original_filename: str | None = None, 
    ) -> IngestionResult:
        document_id = str(uuid.uuid4())
        errors: list[IngestionError] = []

        try:
            file_type = self.detector.detect(source)

            if file_type == FileType.UNKNOWN:
                raise UnsupportedFileTypeError(file_type.value, source)

            extractor = self._extractors.get(file_type)
            if extractor is None:
                raise UnsupportedFileTypeError(file_type.value, source)

            extracted_doc = extractor.extract(source)
            cleaned_doc = self._clean_document(extracted_doc)

            chunks = self.chunker.chunk(
                document_id=document_id,
                pages=cleaned_doc.pages,
                metadata={
                    "document_id": document_id,
                    "user_id": user_id,
                    "source_path": cleaned_doc.source_path,
                    "file_type": cleaned_doc.file_type.value,
                },
            )

            embeddings = self.embedder.embed_documents(
                [chunk.text for chunk in chunks]
            )

            self.vector_store.add(
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata={
                    "document_id": document_id,
                    "user_id": user_id,
                    "file_type": cleaned_doc.file_type.value,
                },
            )

            self.keyword_store.add(
                document_id=document_id,
                chunks=chunks,
            )

            summary = self.summarizer.summarize(cleaned_doc)

            
            display_name = original_filename or self._get_file_name(source)

            result = IngestionResult(
                document_id=document_id,
                file_name=display_name,
                total_chunks=len(chunks),
                summary=summary,
                status="success",
                errors=[],
            )

            self.repository.save(
                result=result,
                extracted_doc=cleaned_doc,
                user_id=user_id,
            )

            return result

        except Exception as exc:
            logger.exception("Ingestion failed. source=%s", source)
            errors.append(
                IngestionError(
                    stage="unknown",
                    message=str(exc),
                    code=exc.__class__.__name__,
                    recoverable=False,
                )
            )
            return IngestionResult(
                document_id=document_id,
                file_name=original_filename or self._get_file_name(source),
                total_chunks=0,
                summary=self._fallback_summary(),
                status="failed",
                errors=errors,
            )

    def _clean_document(self, doc: ExtractedDocument) -> ExtractedDocument:
        cleaned_pages = [self.cleaner.clean(page) for page in doc.pages]
        return doc.model_copy(update={"pages": cleaned_pages})

    @staticmethod
    def _get_file_name(source: str | Path) -> str:
        s = str(source).strip()
        if s.startswith(("http://", "https://")):
            return s
        return Path(s).name

    @staticmethod
    def _fallback_summary() -> DocumentSummary:
        return DocumentSummary(
            short_summary="Ingestion failed before summary could be generated.",
            key_topics=[],
            estimated_difficulty="beginner",
        )