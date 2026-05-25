from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"[{self.provider}] {self.reason}"


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float = 0,
    ) -> str:
        """Return text content from the first LLM choice."""
        raise NotImplementedError
    