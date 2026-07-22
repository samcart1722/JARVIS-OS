"""
Default implementation of the MemoryRanker contract.
"""

from __future__ import annotations

from app.cognition.memory.contracts import MemoryRanker
from app.cognition.memory.domain.entities import (
    MemoryQuery,
    RetrievedMemory,
)


class DefaultRanker(MemoryRanker):
    """
    Default implementation of the MemoryRanker.

    This implementation preserves the order supplied by the retriever.
    Future implementations may apply relevance ordering.
    """

    async def rank(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """Return retrieved memories in their existing order."""
        return memories
