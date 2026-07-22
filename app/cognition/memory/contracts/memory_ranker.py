"""
Contract for ranking retrieved memories.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import (
    MemoryQuery,
    RetrievedMemory,
)


class MemoryRanker(Protocol):
    """
    Orders memories already retrieved by the repository.
    """

    async def rank(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """
        Order retrieved memories.
        """
        ...
