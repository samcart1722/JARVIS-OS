"""
Default implementation of the MemoryExtractor contract.
"""

from __future__ import annotations

from app.cognition.memory.contracts import MemoryExtractor
from app.cognition.memory.domain.entities import MemoryFact
from app.cognition.memory.domain.enums import (
    MemoryCategory,
    MemorySource,
)
from app.cognition.memory.domain.value_objects import (
    MemoryConfidence,
    MemoryId,
)


class DefaultExtractor(MemoryExtractor):
    """
    Basic implementation of the MemoryExtractor.

    This implementation converts the entire input text into a
    single MemoryFact. More sophisticated extractors (LLMs, NLP,
    rule engines, etc.) can replace this implementation later
    without changing the rest of the architecture.
    """

    async def extract(
        self,
        content: str,
    ) -> tuple[MemoryFact, ...]:
        content = content.strip()

        if not content:
            return ()

        memory = MemoryFact(
            id=MemoryId(),
            content=content,
            category=MemoryCategory.CONVERSATION,
            source=MemorySource.USER,
            confidence=MemoryConfidence(1.0),
        )

        return (memory,)
