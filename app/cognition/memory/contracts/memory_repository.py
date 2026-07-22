"""
Contract for persistent memory storage.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import (
    MemoryFact,
    MemoryQuery,
    MemoryResult,
)
from app.cognition.memory.domain.value_objects import MemoryId


class MemoryRepository(Protocol):
    """
    Defines the persistence interface for MemoryFact entities.
    """

    async def save(
        self,
        memory: MemoryFact,
    ) -> None:
        """
        Persist a memory.
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

    async def search(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """
        Search memories matching the supplied query.
        """
        ...

    async def delete(
        self,
        memory_id: MemoryId,
    ) -> None:
        """
        Delete a memory.
        """
        ...

    async def exists(
        self,
        memory_id: MemoryId,
    ) -> bool:
        """
        Check whether a memory exists.
        """
        ...
