from __future__ import annotations
import logging
import os
from groq import Groq
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
    MODEL = "llama-3.1-8b-instant"

    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise SummarizerError("GROQ_API_KEY environment variable is not set")

        self.client = Groq(api_key=api_key)

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
        response = self.client.chat.completions.create(
            model=self.MODEL,
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
            temperature=0,
        )

        content = response.choices[0].message.content

        if not content:
            raise SummarizerError("Groq returned an empty summary response")

        return DocumentSummary.model_validate_json(content)

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