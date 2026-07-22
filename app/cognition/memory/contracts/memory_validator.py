"""
Contract for validating extracted memories.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import MemoryFact


class MemoryValidator(Protocol):
    """
    Validates whether a memory should be persisted.
    """

    async def validate(
        self,
        memory: MemoryFact,
    ) -> bool:
        """
        Return True if the memory is valid.
        """
        ...
