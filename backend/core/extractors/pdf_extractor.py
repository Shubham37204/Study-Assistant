from __future__ import annotations

import logging
from pathlib import Path

import fitz

from schemas.ingestion import ExtractedDocument, ExtractedPage, FileType
from .base_extractor import BaseExtractor, ExtractorError

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    SCANNED_THRESHOLD = 30
    OCR_CONFIDENCE_THRESHOLD = 0.3
    OCR_ZOOM = 2.0

    def __init__(self) -> None:
        self._ocr_reader = None

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

            return ExtractedDocument(
                source_path=str(source_path),
                file_type=FileType.PDF,
                pages=pages,
                title=title,
            )

        except ExtractorError:
            raise 

        except Exception as exc:
            raise ExtractorError(source_path, str(exc)) from exc

        finally:
            if doc is not None:
                doc.close()

    def _extract_page(self, page: fitz.Page, page_number: int) -> ExtractedPage:
        raw_text = page.get_text("text").strip()
        word_count = len(raw_text.split())
        is_scanned = word_count < self.SCANNED_THRESHOLD

        if is_scanned:
            ocr_text = self._ocr_page(page, page_number)
            if len(ocr_text.split()) > word_count:
                raw_text = ocr_text
                word_count = len(raw_text.split())
                logger.info("OCR used for PDF page %s (%s words)", page_number, word_count)

        return ExtractedPage(
            page_number=page_number,
            raw_text=raw_text,
            is_scanned=is_scanned,
        )

    def _ocr_page(self, page: fitz.Page, page_number: int) -> str:
        try:
            import numpy as np

            matrix = fitz.Matrix(self.OCR_ZOOM, self.OCR_ZOOM)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                pixmap.height,
                pixmap.width,
                pixmap.n,
            )

            reader = self._get_ocr_reader()
            results = reader.readtext(image)
            text_parts = [
                text.strip()
                for _bbox, text, confidence in results
                if confidence >= self.OCR_CONFIDENCE_THRESHOLD and text.strip()
            ]
            return " ".join(text_parts)
        except Exception as exc:
            logger.warning("OCR failed for PDF page %s: %s", page_number, exc)
            return ""

    def _get_ocr_reader(self):
        if self._ocr_reader is None:
            import easyocr

            logger.info("Loading EasyOCR model for scanned PDF pages")
            self._ocr_reader = easyocr.Reader(["en"], gpu=False)
        return self._ocr_reader

    @staticmethod
    def _normalize_title(title: str | None) -> str | None:
        if not title:
            return None
        normalized = title.strip()
        return normalized or None
    
