"""
In-memory implementation of the MemoryRepository contract.

This implementation is intended for development and testing.
"""

from __future__ import annotations

from app.cognition.memory.contracts import MemoryRepository
from app.cognition.memory.domain.entities import (
    MemoryFact,
    MemoryQuery,
    MemoryResult,
    RetrievedMemory,
)
from app.cognition.memory.domain.value_objects import MemoryId


class InMemoryRepository(MemoryRepository):
    """
    Simple in-memory repository.
    """

    def __init__(self) -> None:
        self._storage: dict[str, MemoryFact] = {}

    async def save(
        self,
        memory: MemoryFact,
    ) -> None:
        self._storage[str(memory.id)] = memory

    async def get(
        self,
        memory_id: MemoryId,
    ) -> MemoryFact | None:
        return self._storage.get(str(memory_id))

    async def exists(
        self,
        memory_id: MemoryId,
    ) -> bool:
        return str(memory_id) in self._storage

    async def delete(
        self,
        memory_id: MemoryId,
    ) -> None:
        self._storage.pop(str(memory_id), None)

    async def search(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """
        Temporary implementation.

        Returns every active memory.
        Semantic search will be implemented later.
        """

        retrieved = tuple(
            RetrievedMemory(
                memory=memory,
                relevance_score=1.0,
            )
            for memory in self._storage.values()
            if memory.active
        )

        return MemoryResult(
            query=query,
            memories=retrieved,
        )
