"""
Contract for retrieving memories.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import (
    MemoryQuery,
    RetrievedMemory,
)


class MemoryRetriever(Protocol):
    """
    Transforms or filters candidate memories for a query.

    A retriever never accesses persistence. It only transforms or
    filters memories already retrieved by the repository.
    """

    async def retrieve(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """
        Transform or filter retrieved memories.
        """
        ...
