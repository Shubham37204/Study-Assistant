# from __future__ import annotations
# import logging
# import os
# from groq import Groq
# from pydantic import Field
# from schemas.graph import GraphState, Intent
# from schemas.ingestion import StrictBaseModel

# logger = logging.getLogger(__name__)

# class QueryUnderstandingResponse(StrictBaseModel):
#     intent: Intent
#     rewritten_query: str = Field(..., min_length=1)
#     needs_retrieval: bool

# class QueryUnderstandingAgent:
#     MODEL = "llama-3.1-8b-instant"
#     MAX_TOKENS = 300

#     def __init__(self) -> None:
#         api_key = os.getenv("GROQ_API_KEY")

#         if not api_key:
#             logger.warning("GROQ_API_KEY is not set. Query agent will use safe defaults.")
#             self.client: Groq | None = None
#             return

#         self.client = Groq(api_key=api_key)

#     def run(self, state: GraphState) -> dict:
#         query_text = state.get("query_text", "")

#         if not query_text.strip():
#             return self._default_response(query_text)

#         if self.client is None:
#             return self._default_response(query_text)

#         try:
#             response = self.client.chat.completions.create(
#                 model=self.MODEL,
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": self._build_system_prompt(),
#                     },
#                     {
#                         "role": "user",
#                         "content": query_text,
#                     },
#                 ],
#                 temperature=0,
#                 max_completion_tokens=self.MAX_TOKENS,
#             )

#             content = response.choices[0].message.content

#             if not content:
#                 return self._default_response(query_text)

#             return self._parse_response(content, query_text)

#         except Exception:
#             logger.exception("Query understanding failed. query=%r", query_text)
#             return self._default_response(query_text)

#     def _parse_response(self, content: str, original_query: str) -> dict:
#         try:
#             parsed = QueryUnderstandingResponse.model_validate_json(content)

#             return {
#                 "intent": parsed.intent,
#                 "rewritten_query": parsed.rewritten_query,
#                 "needs_retrieval": parsed.needs_retrieval,
#             }

#         except Exception:
#             logger.exception("Failed to parse query understanding response: %r", content)
#             return self._default_response(original_query)

#     @staticmethod
#     def _default_response(query_text: str) -> dict:
#         return {
#             "intent": "factual",
#             "rewritten_query": query_text,
#             "needs_retrieval": True,
#         }

#     @staticmethod
#     def _build_system_prompt() -> str:
#         return """
# You are a query understanding engine.

# Respond ONLY with valid JSON.
# Do not include markdown.
# Do not include explanations.
# Do not wrap the JSON in code fences.

# JSON shape:
# {
#   "intent": "factual | summarize | explain | compare",
#   "rewritten_query": "improved version of the user's question",
#   "needs_retrieval": true
# }

# Rules:
# - intent must be exactly one of: factual, summarize, explain, compare.
# - rewritten_query should be clearer and more specific than the original query.
# - needs_retrieval must be false only for greetings, chitchat, or questions that need no document context.
# - For study questions, document questions, summaries, explanations, comparisons, and factual questions about uploaded material, needs_retrieval must be true.
# """.strip()
    

from __future__ import annotations
import logging
from pydantic import Field
from config import settings
from providers.llm.base import BaseLLMProvider, LLMProviderError
from schemas.graph import GraphState, Intent
from schemas.ingestion import StrictBaseModel
logger = logging.getLogger(__name__)


class QueryUnderstandingResponse(StrictBaseModel):
    intent: Intent
    rewritten_query: str = Field(..., min_length=1)
    needs_retrieval: bool


class QueryUnderstandingAgent:
    MAX_TOKENS = 300

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    def run(self, state: GraphState) -> dict:
        query_text = state.get("query_text", "")

        if not query_text.strip():
            return self._default_response(query_text)

        try:
            content = self.llm.complete(
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": query_text,
                    },
                ],
                model=settings.llm_model_fast,
                max_tokens=self.MAX_TOKENS,
                temperature=0,
            )

            if not content:
                return self._default_response(query_text)

            return self._parse_response(content, query_text)

        except LLMProviderError:
            logger.exception("Query understanding LLM call failed. query=%r", query_text)
            return self._default_response(query_text)

        except Exception:
            logger.exception("Query understanding failed. query=%r", query_text)
            return self._default_response(query_text)

    def _parse_response(self, content: str, original_query: str) -> dict:
        try:
            parsed = QueryUnderstandingResponse.model_validate_json(content)

            return {
                "intent": parsed.intent,
                "rewritten_query": parsed.rewritten_query,
                "needs_retrieval": parsed.needs_retrieval,
            }

        except Exception:
            logger.exception("Failed to parse query understanding response: %r", content)
            return self._default_response(original_query)

    @staticmethod
    def _default_response(query_text: str) -> dict:
        return {
            "intent": "factual",
            "rewritten_query": query_text,
            "needs_retrieval": True,
        }

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are a query understanding engine.

Respond ONLY with valid JSON.
Do not include markdown.
Do not include explanations.
Do not wrap the JSON in code fences.

JSON shape:
{
  "intent": "factual | summarize | explain | compare",
  "rewritten_query": "improved version of the user's question",
  "needs_retrieval": true
}

Rules:
- intent must be exactly one of: factual, summarize, explain, compare.
- rewritten_query should be clearer and more specific than the original query.
- needs_retrieval must be false only for greetings, chitchat, or questions that need no document context.
- For study questions, document questions, summaries, explanations, comparisons, and factual questions about uploaded material, needs_retrieval must be true.
""".strip()