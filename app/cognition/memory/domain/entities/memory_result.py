"""
Represents the result of a memory retrieval operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.cognition.memory.domain.entities.memory_query import MemoryQuery
from app.cognition.memory.domain.entities.retrieved_memory import (
    RetrievedMemory,
)


@dataclass(slots=True)
class MemoryResult:
    """
    Encapsulates the outcome of a memory search.

    A MemoryResult contains the original query, the retrieved
    memories, execution metadata, and convenience properties.
    """

    query: MemoryQuery

    memories: tuple[RetrievedMemory, ...] = field(default_factory=tuple)

    execution_time_ms: float = 0.0

    truncated: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.execution_time_ms < 0:
            raise ValueError("Execution time cannot be negative.")

    @property
    def total_results(self) -> int:
        """Return the number of retrieved memories."""
        return len(self.memories)

    @property
    def is_empty(self) -> bool:
        """Return True if no memories were retrieved."""
        return not self.memories

    @property
    def best_match(self) -> RetrievedMemory | None:
        """Return the highest-ranked memory."""
        if not self.memories:
            return None

        return self.memories[0]
