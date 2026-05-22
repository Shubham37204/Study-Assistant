from __future__ import annotations
from pathlib import Path
from typing import Any
import easyocr
from schemas.ingestion import ExtractedDocument, ExtractedPage, FileType  # ← fixed
from .base_extractor import BaseExtractor, ExtractorError

class ImageExtractor(BaseExtractor):
    CONFIDENCE_THRESHOLD = 0.4

    def __init__(self) -> None:
        self._reader: easyocr.Reader | None = None  # precise type, not Any

    @property
    def reader(self) -> easyocr.Reader:
        if self._reader is None:
            self._reader = easyocr.Reader(["en"])
        return self._reader

    def extract(self, source: str | Path) -> ExtractedDocument:
        source_path = Path(source)

        try:
            results = self.reader.readtext(str(source_path))
            extracted_text = self._join_confident_text(results)

            page = ExtractedPage(
                page_number=1,
                raw_text=extracted_text,
                is_scanned=True,
            )

            return ExtractedDocument(
                source_path=str(source_path),
                file_type=FileType.IMAGE,
                pages=[page],
                # removed: total_pages — computed_field
                title=None,
            )

        except ExtractorError:
            raise

        except Exception as exc:
            raise ExtractorError(source_path, str(exc)) from exc

    def _join_confident_text(self, results: list[Any]) -> str:
        # EasyOCR returns list[list], not list[tuple] — Any is honest here
        text_parts: list[str] = []

        for result in results:
            _bbox, text, confidence = result  # explicit unpack, safer than tuple hint
            if confidence >= self.CONFIDENCE_THRESHOLD:
                cleaned = text.strip()
                if cleaned:
                    text_parts.append(cleaned)

        return "\n".join(text_parts)
    