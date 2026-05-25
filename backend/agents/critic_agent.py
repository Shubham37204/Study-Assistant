from __future__ import annotations
import logging
from pydantic import Field
from config import settings
from providers.llm.base import BaseLLMProvider, LLMProviderError
from schemas.graph import GraphState
from schemas.ingestion import StrictBaseModel

logger = logging.getLogger(__name__)

class CriticResponse(StrictBaseModel):
    is_grounded: bool
    issues: list[str] = Field(default_factory=list)


class CriticAgent:
    MAX_TOKENS = 400
    MAX_CHUNKS_FOR_CRITIC = 3

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    def run(self, state: GraphState) -> dict:
        chunks = state.get("retrieved_chunks", [])
        retry_count = state.get("retry_count", 0)

        if not chunks:
            return {
                "is_grounded": False,
                "critic_issues": ["No retrieved chunks were available to support the answer."],
                "retry_count": retry_count + 1,
            }

        answer = state.get("answer", "")
        formatted_chunks = self._format_chunks_for_critic(state)

        try:
            content = self.llm.complete(
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": f"Answer: {answer}\n\nSources:\n{formatted_chunks}",
                    },
                ],
                model=settings.llm_model_fast,
                max_tokens=self.MAX_TOKENS,
                temperature=0,
            )

            if not content:
                return self._grounded_fallback(retry_count)

            parsed = CriticResponse.model_validate_json(content)

            if parsed.issues:
                logger.info("Critic found grounding issues: %s", parsed.issues)

            return {
                "is_grounded": parsed.is_grounded,
                "critic_issues": parsed.issues,
                "retry_count": retry_count + 1,
            }

        except LLMProviderError:
            logger.exception("Critic LLM call failed. Assuming answer is grounded.")
            return self._grounded_fallback(retry_count)

        except Exception:
            logger.exception("Critic failed. Assuming answer is grounded.")
            return self._grounded_fallback(retry_count)

    def _format_chunks_for_critic(self, state: GraphState) -> str:
        chunks = state.get("retrieved_chunks", [])[: self.MAX_CHUNKS_FOR_CRITIC]
        source_blocks: list[str] = []

        for index, chunk in enumerate(chunks, start=1):
            page_label = chunk.page_number if chunk.page_number is not None else "unknown"
            source_blocks.append(
                f"[SOURCE {index}] (Page {page_label})\n{chunk.text}"
            )

        return "\n\n".join(source_blocks)

    @staticmethod
    def _grounded_fallback(retry_count: int) -> dict:
        return {
            "is_grounded": True,
            "critic_issues": [],
            "retry_count": retry_count,
        }

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are a grounding checker.

Given an answer and source chunks, verify that the answer is supported.

Respond ONLY with valid JSON.
Do not include markdown.
Do not include explanations.
Do not wrap JSON in code fences.

JSON shape:
{
  "is_grounded": true,
  "issues": []
}

Rules:
- is_grounded must be false if the answer contains facts not present in any source chunk.
- is_grounded must be false if the answer contradicts source chunks.
- is_grounded must be false if the answer is vague where sources are specific.
- issues must be an empty list if grounded.
- issues must contain specific problems if not grounded.
""".strip()