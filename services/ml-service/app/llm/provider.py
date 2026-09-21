"""
LlmProvider interface. The invariant that matters more than any single
line of code in this project: the LLM never produces a score, a decision,
or a reason code -- it renders prose from a payload that has already been
retrieved and decided. Every provider implements the same narrow contract.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LlmProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        ...
