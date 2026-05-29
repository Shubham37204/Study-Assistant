from __future__ import annotations
import re
import unicodedata
from schemas.ingestion import ExtractedPage 

class TextCleaner:
    STANDALONE_PAGE_NUMBER_PATTERN = re.compile(
        r"(?m)^\s*(?:-+\s*)?(?:page\s*)?\d+(?:\s*of\s*\d+)?(?:\s*-+)?\s*$",
        re.IGNORECASE,
    )
    COMMON_HEADER_FOOTER_PATTERN = re.compile(
        r"(?mi)^\s*(?:confidential|draft|copyright|all rights reserved)\s*$"
    )
    EXCESSIVE_NEWLINES_PATTERN = re.compile(r"\n{3,}")
    MULTIPLE_SPACES_PATTERN = re.compile(r"[^\S\n\t]{2,}")

    @classmethod
    def clean(cls, page: ExtractedPage) -> ExtractedPage:
        text = page.raw_text
        text = cls._normalize_unicode(text)
        text = cls._remove_page_artifacts(text)
        text = cls._collapse_whitespace(text)
        text = cls._remove_non_printable(text)

        return ExtractedPage(
            page_number=page.page_number,
            raw_text=text,
            is_scanned=page.is_scanned,
        )

    @staticmethod
    def _normalize_unicode(text: str) -> str:
        return unicodedata.normalize("NFKC", text)

    @classmethod
    def _remove_page_artifacts(cls, text: str) -> str:
        text = cls.STANDALONE_PAGE_NUMBER_PATTERN.sub("", text)
        return cls.COMMON_HEADER_FOOTER_PATTERN.sub("", text)

    @classmethod
    def _collapse_whitespace(cls, text: str) -> str:
        text = cls.EXCESSIVE_NEWLINES_PATTERN.sub("\n\n", text)
        text = cls.MULTIPLE_SPACES_PATTERN.sub(" ", text)
        return text.strip()

    @staticmethod
    def _remove_non_printable(text: str) -> str:
        return "".join(
            char
            for char in text
            if char in {"\n", "\t"} or not unicodedata.category(char).startswith("C")
        )