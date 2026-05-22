from __future__ import annotations
import httpx
import trafilatura
from schemas.ingestion import ExtractedDocument, ExtractedPage, FileType  # ← fixed
from .base_extractor import BaseExtractor, ExtractorError


class LinkExtractor(BaseExtractor):
    TIMEOUT_SECONDS = 10

    def extract(self, source: str) -> ExtractedDocument:
        source_url = source.strip()

        if not source_url:
            raise ExtractorError(source, "URL cannot be empty")

        try:
            response = httpx.get(
                source_url,
                timeout=self.TIMEOUT_SECONDS,
                follow_redirects=True,
            )

        except httpx.HTTPError as exc:
            raise ExtractorError(source_url, str(exc)) from exc

        if response.status_code != httpx.codes.OK:
            raise ExtractorError(
                source_url,
                f"HTTP {response.status_code}",
            )

        extracted_text = trafilatura.extract(response.text)

        if not extracted_text:
            raise ExtractorError(source_url, "trafilatura could not extract content")

        title = self._extract_title(response.text, source_url)

        page = ExtractedPage(
            page_number=1,
            raw_text=extracted_text,
            is_scanned=False,
        )

        return ExtractedDocument(
            source_path=source_url,
            file_type=FileType.URL,
            pages=[page],
            # removed: total_pages — computed_field
            title=title,
        )

    @staticmethod
    def _extract_title(html: str, source_url: str) -> str | None:
        metadata = trafilatura.extract_metadata(html, default_url=source_url)

        if metadata is None:
            return None

        title = getattr(metadata, "title", None)
        if not title:
            return None

        normalized = title.strip()
        return normalized or None