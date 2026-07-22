"""
Represents a request to retrieve memories from the Cognitive Memory Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.cognition.memory.domain.enums import MemoryCategory


@dataclass(slots=True)
class MemoryQuery:
    """
    Defines the parameters for retrieving memories.
    """

    text: str

    categories: tuple[MemoryCategory, ...] = field(default_factory=tuple)

    tags: tuple[str, ...] = field(default_factory=tuple)

    limit: int = 10

    minimum_relevance: float = 0.0

    include_inactive: bool = False

    def __post_init__(self) -> None:
        self.text = self.text.strip()

        if not self.text:
            raise ValueError("Query text cannot be empty.")

        if self.limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        if not 0.0 <= self.minimum_relevance <= 1.0:
            raise ValueError("Minimum relevance must be between 0.0 and 1.0.")
