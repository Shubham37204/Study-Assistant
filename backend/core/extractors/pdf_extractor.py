from __future__ import annotations
from pathlib import Path
import fitz
from schemas.ingestion import ExtractedDocument, ExtractedPage, FileType
from .base_extractor import BaseExtractor, ExtractorError

class PDFExtractor(BaseExtractor):
    SCANNED_THRESHOLD = 50

    def extract(self, source: str | Path) -> ExtractedDocument:
        source_path = Path(source)
        doc = None

        try:
            doc = fitz.open(str(source_path))

            pages = [
                self._extract_page(page, page_number=index + 1)
                for index, page in enumerate(doc)
            ]

            metadata: dict[str, str] = getattr(doc, "metadata", {})
            title = self._normalize_title(metadata.get("title"))

            title = self._normalize_title(metadata.get("title"))

            return ExtractedDocument(
                source_path=str(source_path),
                file_type=FileType.PDF,
                pages=pages,
                # removed: total_pages — now computed_field, extra="forbid" would crash
                title=title,
            )

        except ExtractorError:
            raise  # don't re-wrap our own errors

        except Exception as exc:
            raise ExtractorError(source_path, str(exc)) from exc

        finally:
            if doc is not None:
                doc.close()

    def _extract_page(self, page: fitz.Page, page_number: int) -> ExtractedPage:
        raw_text = page.get_text("text")
        word_count = len(raw_text.split())

        return ExtractedPage(
            page_number=page_number,
            raw_text=raw_text,
            is_scanned=word_count < self.SCANNED_THRESHOLD,
        )

    @staticmethod
    def _normalize_title(title: str | None) -> str | None:
        if not title:
            return None
        normalized = title.strip()
        return normalized or None
    