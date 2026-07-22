"""
High-level contract for the Cognitive Memory Engine.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import (
    MemoryFact,
    MemoryQuery,
    MemoryResult,
)
from app.cognition.memory.domain.value_objects import MemoryId


class MemoryPipeline(Protocol):
    """
    Coordinates the complete memory lifecycle.
    """

    async def remember(
        self,
        content: str,
    ) -> tuple[MemoryFact, ...]:
        """
        Extract, validate, classify and persist memories.
        """
        ...

    async def recall(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """
        Retrieve relevant memories.
        """
        ...

    async def get(
        self,
        memory_id: MemoryId,
    ) -> MemoryFact | None:
        """
        Retrieve a memory by its identifier.
        """
        ...

    async def forget(
        self,
        memory_id: MemoryId,
    ) -> None:
        """
        Remove a memory from storage.
        """
        ...
