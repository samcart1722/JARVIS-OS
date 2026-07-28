"""Temporary bridge from the legacy memory surface to Cognitive Memory."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.cognition.memory.contracts import MemoryPipeline
from app.cognition.memory.domain.entities import MemoryQuery


@dataclass(frozen=True, slots=True)
class LegacyMemoryFact:
    """Temporary legacy projection of a Cognitive Memory fact."""

    key: str
    value: str


class LegacyMemoryAdapter:
    """
    Temporary compatibility adapter for legacy ReasoningEngine consumers.

    This adapter preserves the legacy memory surface while delegating storage
    and retrieval to the Cognitive Memory Pipeline. It shall be removed when
    ReasoningEngine consumes the public Cognitive Memory contract directly.
    """

    def __init__(self, pipeline: MemoryPipeline) -> None:
        self._pipeline = pipeline

    def remember(self, key: str, value: str) -> None:
        """Persist a legacy key-value fact through the Memory Pipeline."""
        normalized_value = value.strip().rstrip(".,;:!?")
        self._run(self._pipeline.remember(f"{key}: {normalized_value}"))

    def knowledge(self) -> tuple[LegacyMemoryFact, ...]:
        """Project memories from the pipeline into the temporary legacy view."""
        return self._recall_all()

    def answer(self, user_input: str) -> str | None:
        """Preserve the legacy answer behavior using pipeline-backed facts."""
        facts = {fact.key: fact.value for fact in self._recall_all()}
        text = user_input.casefold()

        if "proyecto principal" in text or "cual es mi proyecto" in text:
            value = facts.get("project")
            return (
                f"Tu proyecto principal es {value}."
                if value
                else "Todavía no conozco tu proyecto principal."
            )

        if "profesion" in text or "cual es mi profesion" in text:
            value = facts.get("profession")
            return (
                f"Tu profesión es {value}."
                if value
                else "Todavía no conozco tu profesión."
            )

        return None

    def _recall_all(self) -> tuple[LegacyMemoryFact, ...]:
        result = self._run(self._pipeline.recall(MemoryQuery(text="legacy")))
        facts: list[LegacyMemoryFact] = []

        for retrieved in result.memories:
            key, separator, value = retrieved.memory.content.partition(": ")
            if separator and key and value:
                facts.append(LegacyMemoryFact(key=key, value=value))

        return tuple(facts)

    @staticmethod
    def _run(coroutine):
        return asyncio.run(coroutine)
