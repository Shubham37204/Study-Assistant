from __future__ import annotations

import logging

from config import settings
from providers.llm.base import BaseLLMProvider, LLMProviderError
from schemas.ingestion import DocumentSummary, ExtractedDocument

logger = logging.getLogger(__name__)


class SummarizerError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"[SummarizerError] {self.reason}"


class DocumentSummarizer:
    MAX_CHARS_DIRECT = 6000
    MAX_CHARS_MAPREDUCE = 60000
    MAX_TOKENS = 400

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    def summarize(self, doc: ExtractedDocument) -> DocumentSummary:
        text = self._join_page_text(doc)

        if not text:
            return DocumentSummary(
                short_summary="No readable text was extracted from this document.",
                key_topics=[],
                estimated_difficulty="beginner",
            )

        if len(text) <= self.MAX_CHARS_DIRECT:
            return self._summarize_direct(text)

        logger.warning(
            "Document exceeds direct summarization limit. "
            "Truncating to first 10 pages. source_path=%s total_chars=%s",
            doc.source_path,
            len(text),
        )

        return self._summarize_truncated(doc)

    def _summarize_direct(self, text: str) -> DocumentSummary:
        try:
            content = self.llm.complete(
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                model=settings.llm_model_fast,
                max_tokens=self.MAX_TOKENS,
                temperature=0,
            )

        except LLMProviderError as exc:
            raise SummarizerError(str(exc)) from exc

        if not content:
            raise SummarizerError("LLM returned an empty summary response")

        try:
            return DocumentSummary.model_validate_json(content)

        except Exception as exc:
            raise SummarizerError(f"Failed to parse summary JSON: {exc}") from exc

    def _summarize_truncated(self, doc: ExtractedDocument) -> DocumentSummary:
        truncated_text = "\n\n".join(
            page.raw_text
            for page in doc.pages[:10]
            if page.raw_text.strip()
        )

        if len(truncated_text) > self.MAX_CHARS_MAPREDUCE:
            truncated_text = truncated_text[: self.MAX_CHARS_MAPREDUCE]

        return self._summarize_direct(truncated_text)

    @staticmethod
    def _join_page_text(doc: ExtractedDocument) -> str:
        return "\n\n".join(page.raw_text for page in doc.pages if page.raw_text.strip())

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are a document summarization service.

Respond ONLY with valid JSON.
Do not include markdown.
Do not include explanations.
Do not wrap the JSON in code fences.

The JSON must exactly match this shape:
{
  "short_summary": "string, maximum 200 characters",
  "key_topics": ["string", "maximum 10 items"],
  "estimated_difficulty": "beginner | intermediate | advanced"
}

Rules:
- short_summary must be concise and useful for a study assistant.
- key_topics must contain the most important topics from the document.
- estimated_difficulty must be exactly one of: beginner, intermediate, advanced.
""".strip()
    