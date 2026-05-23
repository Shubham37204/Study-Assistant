from __future__ import annotations
from schemas.chunk import Chunk              
from schemas.ingestion import ExtractedPage 

class Chunker:
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50

    def chunk(
        self,
        document_id: str,
        pages: list[ExtractedPage],
        metadata: dict[str, str],
    ) -> list[Chunk]:
        segments: list[tuple[str, int | None]] = []

        for page in pages:
            for segment in self._split_page(page):
                segments.append((segment, page.page_number))

        chunks = self._build_chunks(
            segments=segments,
            document_id=document_id,
            metadata=metadata,
        )

        total_chunks = len(chunks)

        return [
            chunk.model_copy(update={"total_chunks": total_chunks})
            for chunk in chunks
        ]

    def _split_page(self, page: ExtractedPage) -> list[str]:
        paragraphs = [
            paragraph.strip()
            for paragraph in page.raw_text.split("\n\n")
            if paragraph.strip()
        ]

        segments: list[str] = []

        for paragraph in paragraphs:
            if len(paragraph) <= self.CHUNK_SIZE:
                segments.append(paragraph)
                continue
            segments.extend(self._split_long_paragraph(paragraph))

        return segments

    def _split_long_paragraph(self, paragraph: str) -> list[str]:
        sentences = [
            sentence.strip()
            for sentence in paragraph.split(". ")
            if sentence.strip()
        ]

        segments: list[str] = []
        current_text = ""

        for sentence in sentences:
            if not sentence.endswith("."):
                sentence = f"{sentence}."

            if len(sentence) > self.CHUNK_SIZE:
                if current_text:
                    segments.append(current_text.strip())
                    current_text = ""
                segments.extend(self._split_long_text(sentence))
                continue

            candidate = self._join_text(current_text, sentence)

            if len(candidate) <= self.CHUNK_SIZE:
                current_text = candidate
            else:
                if current_text:
                    segments.append(current_text.strip())
                current_text = sentence

        if current_text.strip():
            segments.append(current_text.strip())

        return segments

    def _split_long_text(self, text: str) -> list[str]:
        segments: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE
            segment = text[start:end].strip()
            if segment:
                segments.append(segment)
            start = end

        return segments

    def _build_chunks(
        self,
        segments: list[tuple[str, int | None]],
        document_id: str,
        metadata: dict[str, str],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        current_text = ""
        current_page: int | None = None
        chunk_index = 0

        for segment, page_number in segments:
            candidate = self._join_text(current_text, segment)

            if len(candidate) <= self.CHUNK_SIZE:
                current_text = candidate
                if current_page is None:
                    current_page = page_number
                continue

            if current_text.strip():
                chunks.append(
                    self._create_chunk(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        text=current_text,
                        page_number=current_page,
                        metadata=metadata,
                    )
                )
                chunk_index += 1

            overlap_text = current_text[-self.CHUNK_OVERLAP:] if current_text else ""
            current_text = self._join_text(overlap_text, segment)
            current_page = page_number

        if current_text.strip():
            chunks.append(
                self._create_chunk(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    text=current_text,
                    page_number=current_page,
                    metadata=metadata,
                )
            )

        return chunks

    @staticmethod
    def _join_text(left: str, right: str) -> str:
        left = left.strip()
        right = right.strip()
        if not left:
            return right
        if not right:
            return left
        return f"{left}\n\n{right}"

    @staticmethod
    def _create_chunk(
        document_id: str,
        chunk_index: int,
        text: str,
        page_number: int | None,
        metadata: dict[str, str],
    ) -> Chunk:
        return Chunk(
            chunk_id=f"{document_id}_{chunk_index}",
            document_id=document_id,
            text=text.strip(),
            page_number=page_number,
            chunk_index=chunk_index,
            metadata=dict(metadata),
        )
    