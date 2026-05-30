from __future__ import annotations
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Document, Page
from schemas.ingestion import ExtractedDocument, IngestionResult 

class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(
        self,
        result: IngestionResult,
        extracted_doc: ExtractedDocument,
        user_id: str,
    ) -> Document:
        document = Document(
            id=result.document_id,
            user_id=user_id,
            file_name=result.file_name,
            file_type=extracted_doc.file_type.value,
            title=extracted_doc.title,
            total_pages=extracted_doc.total_pages,
            total_chunks=result.total_chunks,
            short_summary=result.summary.short_summary,
            key_topics=",".join(result.summary.key_topics),
            status=result.status,
        )

        document.pages = [
            Page(
                id=str(uuid4()),
                document_id=result.document_id,
                page_number=page.page_number,
                word_count=page.word_count,
                is_scanned=page.is_scanned,
            )
            for page in extracted_doc.pages
        ]

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, document_id: str) -> Document | None:
        return self.db.get(Document, document_id)

    def list_by_user(self, user_id: str) -> list[Document]:
        statement = (
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def delete(self, document_id: str) -> bool:
        document = self.get_by_id(document_id)
        if document is None:
            return False
        self.db.delete(document)
        self.db.commit()
        return True