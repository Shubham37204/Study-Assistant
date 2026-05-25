from __future__ import annotations

from groq import APIError, Groq

from config import settings
from providers.llm.base import BaseLLMProvider, LLMProviderError


class GroqProvider(BaseLLMProvider):
    PROVIDER_NAME = "groq"

    def __init__(self, api_key: str | None = None) -> None:
        resolved_api_key = api_key or settings.groq_api_key
        self.client = Groq(api_key=resolved_api_key)

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float = 0,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content

            return content or ""

        except APIError as exc:
            raise LLMProviderError(self.PROVIDER_NAME, str(exc)) from exc

        except Exception as exc:
            raise LLMProviderError(self.PROVIDER_NAME, str(exc)) from exc
        