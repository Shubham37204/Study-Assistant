from __future__ import annotations

from typing import Literal, TypedDict
from schemas.retrieval import ChunkResult, SearchQuery

Intent = Literal["factual", "summarize", "explain", "compare", "greeting"]


class Citation(TypedDict):
    chunk_id: str
    document_id: str
    page_number: int | None
    excerpt: str


class ConversationTurn(TypedDict):
    role: str
    content: str


class GraphState(TypedDict, total=False):
    user_id: str
    query_text: str
    document_ids: list[str]
    conversation_history: list[ConversationTurn]


    intent: Intent
    rewritten_query: str
    needs_retrieval: bool

    search_query: SearchQuery | None


    retrieved_chunks: list[ChunkResult]
    total_candidates: int

    answer: str
    citations: list[Citation]
    confidence: float


    is_grounded: bool
    critic_issues: list[str]
    retry_count: int


    final_answer: str
    final_citations: list[Citation]
    