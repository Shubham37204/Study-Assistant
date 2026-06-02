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
        self.query_agent      = QueryUnderstandingAgent(llm=llm)
        self.planning_agent   = PlanningAgent()
        self.retrieval_agent  = RetrievalAgent(
            embedder=embedder,
            vector_store=vector_store,
            bm25_store=keyword_store,
            reranker=reranker,
        )
        self.generation_agent = GenerationAgent(llm=llm)
        self.critic_agent     = CriticAgent(llm=llm)
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        graph = StateGraph(GraphState)

        graph.add_node("query_understanding", self._run_query_agent)
        graph.add_node("planning",            self._run_planning_agent)
        graph.add_node("retrieval",           self._run_retrieval_agent)
        graph.add_node("generation",          self._run_generation_agent)
        graph.add_node("critic",              self._run_critic_agent)
        graph.add_node("finalize",            self._finalize)

        graph.set_entry_point("query_understanding")
        graph.add_edge("query_understanding", "planning")
        graph.add_edge("planning",            "retrieval")
        graph.add_edge("retrieval",           "generation")
        graph.add_edge("generation",          "critic")
        graph.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {"retrieval": "retrieval", "finalize": "finalize"},
        )
        graph.add_edge("finalize", END)

        return graph.compile()

    def _route_after_critic(self, state: GraphState) -> str:
        if not state.get("is_grounded", True) and state.get("retry_count", 0) < settings.critic_max_retries:
            logger.info("Retrying retrieval. retry_count=%s", state.get("retry_count"))
            return "retrieval"
        return "finalize"

    def _finalize(self, state: GraphState) -> dict:
        return {
            "final_answer":    state.get("answer", ""),
            "final_citations": state.get("citations", []),
        }

    def _run_query_agent(self, state: GraphState) -> dict:
        try:
            result = self.query_agent.run(state)
            if state.get("document_ids"):
                result["needs_retrieval"] = True
            logger.info("Query agent completed. intent=%s", result.get("intent"))
            return result
        except Exception as e:
            logger.exception("Query agent failed: %s", str(e))
            raise
    
    def _run_planning_agent(self, state: GraphState) -> dict:
        try:
            result = self.planning_agent.run(state)
            logger.info("Planning agent completed. search_type=%s", 
                       result.get("search_query").search_type if result.get("search_query") else None)
            return result
        except Exception as e:
            logger.exception("Planning agent failed: %s", str(e))
            raise

    def _run_retrieval_agent(self, state: GraphState) -> dict:
        search_query = state.get("search_query")
        if not search_query:
            logger.warning("search_query missing — skipping retrieval")
            return {"retrieved_chunks": [], "total_candidates": 0}
        try:
            result = self.retrieval_agent.run(search_query)
            return {
                "retrieved_chunks": result.chunks,
                "total_candidates": result.total_candidates_before_rerank,
            }
        except Exception as e:
            logger.exception("Retrieval agent failed: %s", str(e))
            return {"retrieved_chunks": [], "total_candidates": 0}

    def _run_generation_agent(self, state: GraphState) -> dict:
        try:
            result = self.generation_agent.run(state)
            logger.info("Generation agent completed. answer_length=%d", len(result.get("answer", "")))
            return result
        except Exception as e:
            logger.exception("Generation agent failed: %s", str(e))
            raise

    def _run_critic_agent(self, state: GraphState) -> dict:
        try:
            result = self.critic_agent.run(state)
            logger.info("Critic agent completed. is_grounded=%s", result.get("is_grounded"))
            return result
        except Exception as e:
            logger.exception("Critic agent failed: %s", str(e))
            raise

    def query(
        self,
        user_id: str,
        query_text: str,
        document_ids: list[str] | None = None,
        conversation_history: list[dict] | None = None, 
    ) -> dict:
        logger.info("Starting query. user_id=%s query=%r doc_ids=%s", user_id, query_text, document_ids)
        
        initial_state: GraphState = {
            "user_id":              user_id,
            "query_text":           query_text,
            "document_ids":         document_ids or [],
            "conversation_history": conversation_history or [], 
            "retry_count":          0,
            "needs_retrieval":      True,
            "retrieved_chunks":     [],
            "critic_issues":        [],
            "citations":            [],
            "final_citations":      [],
        }

        try:
            final_state = self.graph.invoke(initial_state)
        except Exception as e:
            logger.exception("Graph invocation failed: %s", str(e))
            raise

        logger.info("Query completed. answer_length=%d citations=%d", 
                   len(final_state.get("final_answer", "")), 
                   len(final_state.get("final_citations", [])))

        return {
            "answer":    final_state.get("final_answer", ""),
            "citations": final_state.get("final_citations", []),
            "intent":    final_state.get("intent", "factual"),
        }
    