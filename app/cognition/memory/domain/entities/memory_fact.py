"""
Core domain entity representing a persistent memory.

A MemoryFact is the fundamental unit of knowledge stored by the
Cognitive Memory Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.cognition.memory.domain.enums import (
    MemoryCategory,
    MemorySource,
)
from app.cognition.memory.domain.value_objects import (
    MemoryConfidence,
    MemoryId,
)


@dataclass(slots=True)
class MemoryFact:
    """
    Represents a persistent piece of knowledge.

    The content of a memory is immutable after creation.
    Operational attributes (confidence, tags, metadata, etc.)
    may evolve over time.
    """

    id: MemoryId
    content: str
    category: MemoryCategory
    source: MemorySource
    confidence: MemoryConfidence

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    tags: set[str] = field(default_factory=set)

    metadata: dict[str, Any] = field(default_factory=dict)

    version: int = 1

    active: bool = True

    def __post_init__(self) -> None:
        self.content = self.content.strip()

        if not self.content:
            raise ValueError("Memory content cannot be empty.")

    def deactivate(self) -> None:
        """Deactivate this memory."""
        self.active = False
        self.touch()

    def activate(self) -> None:
        """Activate this memory."""
        self.active = True
        self.touch()

    def update_confidence(
        self,
        confidence: MemoryConfidence,
    ) -> None:
        """Update the confidence score."""
        self.confidence = confidence
        self.increment_version()

    def add_tag(self, tag: str) -> None:
        """Attach a tag."""
        tag = tag.strip().lower()

        if tag:
            self.tags.add(tag)
            self.touch()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag."""
        self.tags.discard(tag.lower())
        self.touch()

    def touch(self) -> None:
        """Update modification timestamp."""
        self.updated_at = datetime.now(UTC)

    def increment_version(self) -> None:
        """Increase entity version."""
        self.version += 1
        self.touch()
