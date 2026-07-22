"""
Contract for classifying memories.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import MemoryFact


class MemoryClassifier(Protocol):
    """
    Assigns semantic categories to memories.
    """

    async def classify(
        self,
        memory: MemoryFact,
    ) -> MemoryFact:
        """
        Return the classified memory.
        """
        ...
