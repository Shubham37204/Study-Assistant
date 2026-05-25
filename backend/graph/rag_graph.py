from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents.critic_agent import CriticAgent
from agents.generation_agent import GenerationAgent
from agents.planning_agent import PlanningAgent
from agents.query_agent import QueryUnderstandingAgent
from agents.retrieval_agent import RetrievalAgent
from config import settings
from providers.embeddings.base import BaseEmbedder
from providers.keyword.base import BaseKeywordStore
from providers.llm.base import BaseLLMProvider
from providers.vectorstores.base import BaseVectorStore
from schemas.graph import GraphState

logger = logging.getLogger(__name__)


class RAGGraph:
    def __init__(
        self,
        llm: BaseLLMProvider,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        keyword_store: BaseKeywordStore,
        reranker: Any,
    ) -> None:
        self.query_agent = QueryUnderstandingAgent(llm=llm)
        self.planning_agent = PlanningAgent()
        self.retrieval_agent = RetrievalAgent(
            embedder=embedder,
            vector_store=vector_store,
            bm25_store=keyword_store,
            reranker=reranker,
        )
        self.generation_agent = GenerationAgent(llm=llm)
        self.critic_agent = CriticAgent(llm=llm)
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(GraphState)

        graph.add_node("query_understanding", self._run_query_agent)
        graph.add_node("planning", self._run_planning_agent)
        graph.add_node("retrieval", self._run_retrieval_agent)
        graph.add_node("generation", self._run_generation_agent)
        graph.add_node("critic", self._run_critic_agent)
        graph.add_node("finalize", self._finalize)

        graph.set_entry_point("query_understanding")

        graph.add_edge("query_understanding", "planning")
        graph.add_edge("planning", "retrieval")
        graph.add_edge("retrieval", "generation")
        graph.add_edge("generation", "critic")

        graph.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {
                "retrieval": "retrieval",
                "finalize": "finalize",
            },
        )

        graph.add_edge("finalize", END)

        return graph.compile()

    def _route_after_critic(self, state: GraphState) -> str:
        is_grounded = state.get("is_grounded", True)
        retry_count = state.get("retry_count", 0)

        if not is_grounded and retry_count < settings.critic_max_retries:
            logger.info(
                "Retrying retrieval after critic failure. retry_count=%s max_retries=%s",
                retry_count,
                settings.critic_max_retries,
            )
            return "retrieval"

        return "finalize"

    def _finalize(self, state: GraphState) -> dict:
        return {
            "final_answer": state.get("answer", ""),
            "final_citations": state.get("citations", []),
        }

    def _run_query_agent(self, state: GraphState) -> dict:
        return self.query_agent.run(state)

    def _run_planning_agent(self, state: GraphState) -> dict:
        return self.planning_agent.run(state)

    def _run_retrieval_agent(self, state: GraphState) -> dict:
        search_query = state.get("search_query")

        if search_query is None:
            logger.warning("Retrieval skipped because search_query is missing.")
            return {
                "retrieved_chunks": [],
                "total_candidates": 0,
            }

        result = self.retrieval_agent.run(search_query)

        return {
            "retrieved_chunks": result.chunks,
            "total_candidates": result.total_candidates_before_rerank,
        }

    def _run_generation_agent(self, state: GraphState) -> dict:
        return self.generation_agent.run(state)

    def _run_critic_agent(self, state: GraphState) -> dict:
        return self.critic_agent.run(state)

    def query(
        self,
        user_id: str,
        query_text: str,
        document_ids: list[str] | None = None,
    ) -> dict:
        initial_state: GraphState = {
            "user_id": user_id,
            "query_text": query_text,
            "document_ids": document_ids or [],
            "retry_count": 0,
            "needs_retrieval": True,
            "retrieved_chunks": [],
            "critic_issues": [],
            "citations": [],
            "final_citations": [],
        }

        final_state = self.graph.invoke(initial_state)

        return {
            "answer": final_state.get("final_answer", ""),
            "citations": final_state.get("final_citations", []),
            "intent": final_state.get("intent", "factual"),
        }