"""
Represents a memory retrieved for a specific query.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.cognition.memory.domain.entities.memory_fact import MemoryFact


@dataclass(slots=True)
class RetrievedMemory:
    """
    A MemoryFact enriched with retrieval metadata.

    Retrieval metadata is ephemeral and only valid during
    the execution of a specific query.
    """

    memory: MemoryFact

    relevance_score: float

    semantic_distance: float | None = None

    matched_terms: tuple[str, ...] = field(default_factory=tuple)

    rank_position: int | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0.")

        if self.semantic_distance is not None:
            if self.semantic_distance < 0:
                raise ValueError("Semantic distance cannot be negative.")
