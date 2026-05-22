from __future__ import annotations
from pathlib import Path
from schemas.ingestion import ExtractedDocument, ExtractedPage, FileType
from .base_extractor import BaseExtractor, ExtractorError
_MARKDOWN_SUFFIXES = {".md", ".markdown"}

class TextExtractor(BaseExtractor):
    """Handles FileType.TEXT and FileType.MARKDOWN — plain files, no parsing needed."""

    def extract(self, source: str | Path) -> ExtractedDocument:
        source_path = Path(source)

        try:
            # errors="replace" → never crashes on encoding edge cases
            raw_text = source_path.read_text(encoding="utf-8", errors="replace")

            suffix = source_path.suffix.lower()
            file_type = (
                FileType.MARKDOWN if suffix in _MARKDOWN_SUFFIXES else FileType.TEXT
            )

            page = ExtractedPage(
                page_number=1,
                raw_text=raw_text,
                is_scanned=False,
            )

            return ExtractedDocument(
                source_path=str(source_path),
                file_type=file_type,
                pages=[page],
                title=source_path.stem,  # filename without extension as title
            )

        except ExtractorError:
            raise

        except Exception as exc:
            raise ExtractorError(source_path, str(exc)) from exc