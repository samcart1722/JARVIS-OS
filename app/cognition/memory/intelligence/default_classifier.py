"""
Default implementation of the MemoryClassifier contract.
"""

from __future__ import annotations

from app.cognition.memory.contracts import MemoryClassifier
from app.cognition.memory.domain.entities import MemoryFact


class DefaultClassifier(MemoryClassifier):
    """
    Basic implementation of the MemoryClassifier.

    The initial implementation preserves the memory unchanged.
    Future implementations may classify memories using rules,
    embeddings, or large language models.
    """

    async def classify(
        self,
        memory: MemoryFact,
    ) -> MemoryFact:
        return memory
