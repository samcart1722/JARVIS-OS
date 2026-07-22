"""
Default implementation of the MemoryRetriever contract.
"""

from __future__ import annotations

from app.cognition.memory.contracts import MemoryRetriever
from app.cognition.memory.domain.entities import (
    MemoryQuery,
    RetrievedMemory,
)


class DefaultRetriever(MemoryRetriever):
    """
    Default implementation of the MemoryRetriever.

    This implementation returns retrieved memories unchanged.
    Future implementations may transform or filter the memories.
    """

    async def retrieve(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """
        Transform or filter retrieved memories.
        """

        return memories
