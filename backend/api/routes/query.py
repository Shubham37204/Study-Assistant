# backend/api/routes/query.py — full updated
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_rag_graph
from graph.rag_graph import RAGGraph
from middleware.clerk_auth import get_verified_user_id
from schemas.api import CitationResponse, ErrorResponse, QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"])
logger = logging.getLogger(__name__)


@router.post("", response_model=QueryResponse)
async def query_documents(
    body: QueryRequest,
    verified_id: str | None = Depends(get_verified_user_id),
    rag_graph: RAGGraph = Depends(get_rag_graph),
) -> QueryResponse:

    effective_user_id = verified_id or body.user_id

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: rag_graph.query(
                user_id=effective_user_id,
                query_text=body.query_text,
                document_ids=body.document_ids,
                conversation_history=[
                    {"role": m.role, "content": m.content}
                    for m in body.conversation_history
                ],
            ),
        )

        citations = [CitationResponse(**c) for c in response.get("citations", [])]

        return QueryResponse(
            answer=response.get("answer", ""),
            citations=citations,
            intent=response.get("intent", "factual"),
            search_type_used=body.search_type,
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Query failed")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="query_failed",
                detail="Failed to process query",
            ).model_dump(),
        )