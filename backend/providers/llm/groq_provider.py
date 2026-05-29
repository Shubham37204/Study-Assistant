from __future__ import annotations

from groq import APIError, APIStatusError, Groq

from config import settings
from providers.llm.base import BaseLLMProvider, LLMProviderError


class GroqProvider(BaseLLMProvider):
    PROVIDER_NAME = "groq"

    def __init__(self, api_key: str | None = None) -> None:
        resolved = api_key or settings.groq_api_key
        self.client = Groq(api_key=resolved)

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
            return response.choices[0].message.content or ""

        except APIStatusError as exc:
            if exc.status_code == 429:
                raise LLMProviderError(
                    self.PROVIDER_NAME,
                    "Rate limit reached. Wait 30 seconds and try again.",
                ) from exc
            raise LLMProviderError(self.PROVIDER_NAME, str(exc)) from exc

        except APIError as exc:
            raise LLMProviderError(self.PROVIDER_NAME, str(exc)) from exc

        except Exception as exc:
            raise LLMProviderError(self.PROVIDER_NAME, str(exc)) from exc
        