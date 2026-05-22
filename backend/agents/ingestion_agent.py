from __future__ import annotations
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
from schemas.ingestion import (   # ← fixed
    DocumentSummary,
    ExtractedDocument,
    FileType,
    IngestionError,
    IngestionResult,
)


class UnsupportedFileTypeError(Exception):  # ← defined here, not imported from self
    def __init__(self, file_type: str, source: str | Path) -> None:
        self.file_type = file_type
        self.source = str(source)
        super().__init__(f"Unsupported file type '{file_type}' for source: {self.source}")


class IngestionAgent:
    def __init__(
        self,
        repository: DocumentRepository,
        chunker: Any,
        embedder: Any,
        vector_store: Any,
        bm25_store: Any,
    ) -> None:
        self.detector = FileDetector()
        self.cleaner = TextCleaner()
        self.summarizer = DocumentSummarizer()
        self.repository = repository
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25_store = bm25_store

        self._extractors: dict[FileType, BaseExtractor] = {
            FileType.PDF: PDFExtractor(),
            FileType.IMAGE: ImageExtractor(),
            FileType.URL: LinkExtractor(),
            FileType.TEXT: TextExtractor(),
            FileType.MARKDOWN: TextExtractor(),
        }

    def run(self, source: str | Path, user_id: str) -> IngestionResult:
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

            self.bm25_store.add(
                document_id=document_id,
                chunks=chunks,
            )

            summary = self.summarizer.summarize(cleaned_doc)

            result = IngestionResult(
                document_id=document_id,
                file_name=self._get_file_name(source),
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
                file_name=self._get_file_name(source),
                total_chunks=0,
                summary=self._fallback_summary(),
                status="failed",
                errors=errors,
            )

    def _clean_document(self, doc: ExtractedDocument) -> ExtractedDocument:
        cleaned_pages = [self.cleaner.clean(page) for page in doc.pages]

        return doc.model_copy(
            update={"pages": cleaned_pages}
            # removed: "total_pages" — computed_field, derived from pages automatically
        )

    @staticmethod
    def _get_file_name(source: str | Path) -> str:
        source_str = str(source).strip()
        if source_str.startswith(("http://", "https://")):
            return source_str
        return Path(source_str).name

    @staticmethod
    def _fallback_summary() -> DocumentSummary:
        return DocumentSummary(
            short_summary="Ingestion failed before a summary could be generated.",
            key_topics=[],
            estimated_difficulty="beginner",
        )