from __future__ import annotations
import logging
from schemas.graph import GraphState, Intent
from schemas.retrieval import SearchQuery, SearchType
logger = logging.getLogger(__name__)


class PlanningAgent:
    INTENT_TO_SEARCH_TYPE: dict[str, SearchType] = {
        "factual": "hybrid",
        "explain": "vector_only",
        "summarize": "vector_only",
        "compare": "hybrid",
    }
    DEFAULT_SEARCH_TYPE: SearchType = "hybrid"

    def run(self, state: GraphState) -> dict:
        query_text = state.get("rewritten_query") or state.get("query_text", "")
        user_id = state.get("user_id", "")
        document_ids = state.get("document_ids", [])
        intent = state.get("intent", "factual")

        search_type = self.INTENT_TO_SEARCH_TYPE.get(
            intent,
            self.DEFAULT_SEARCH_TYPE,
        )

        top_k = 5
        vector_fetch_k = 20

        if state.get("needs_retrieval") is False:
            search_type = "vector_only"
            top_k = 1
            vector_fetch_k = 5

        search_query = SearchQuery(
            query_text=query_text,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
            vector_fetch_k=vector_fetch_k,
            search_type=search_type,
        )

        logger.info(
            "Planning completed. intent=%s search_type=%s top_k=%s vector_fetch_k=%s",
            intent,
            search_type,
            top_k,
            vector_fetch_k,
        )

        return {"search_query": search_query}