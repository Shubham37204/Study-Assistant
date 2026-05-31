from __future__ import annotations
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from schemas.ingestion import FileType

class FileDetector:
    MIME_TYPE_MAPPING: dict[str, FileType] = {
        "application/pdf": FileType.PDF,
        "text/plain": FileType.TEXT,
        "text/markdown": FileType.MARKDOWN,
        "image/png": FileType.IMAGE,
        "image/jpeg": FileType.IMAGE,
        "image/webp": FileType.IMAGE,
        "image/tiff": FileType.IMAGE,
        "image/bmp": FileType.IMAGE,
    }

    EXTENSION_FALLBACK: dict[str, FileType] = {
        ".md": FileType.MARKDOWN,
        ".markdown": FileType.MARKDOWN,
    }

    @classmethod
    def detect(cls, source: str | Path) -> FileType:
        source_str = str(source).strip()

        if not source_str:
            return FileType.UNKNOWN

        parsed = urlparse(source_str)
        if parsed.scheme in {"http", "https"}:
            return FileType.URL

        suffix = Path(source_str).suffix.lower()
        if suffix in cls.EXTENSION_FALLBACK:
            return cls.EXTENSION_FALLBACK[suffix]

        mime_type, _ = mimetypes.guess_type(source_str)
        if mime_type is None:
            return FileType.UNKNOWN

        return cls.MIME_TYPE_MAPPING.get(mime_type, FileType.UNKNOWN)
    