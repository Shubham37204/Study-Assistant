from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_rag_graph
from graph.rag_graph import RAGGraph
from schemas.api import (
    CitationResponse,
    ErrorResponse,
    QueryRequest,
    QueryResponse,
)

router = APIRouter(prefix="/query", tags=["query"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def query_documents(
    body: QueryRequest,
    rag_graph: RAGGraph = Depends(get_rag_graph),
) -> QueryResponse:
    try:
        loop = asyncio.get_running_loop()

        response = await loop.run_in_executor(
            None,
            lambda: rag_graph.query(
                user_id=body.user_id,
                query_text=body.query_text,
                document_ids=body.document_ids,
            ),
        )

        citations = [
            CitationResponse(**citation)
            for citation in response.get("citations", [])
        ]

        return QueryResponse(
            answer=response.get("answer", ""),
            citations=citations,
            intent=response.get("intent", "factual"),
            search_type_used=body.search_type,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Query route failed.")

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="query_failed",
                detail="Failed to process query.",
            ).model_dump(),
        ) from exc