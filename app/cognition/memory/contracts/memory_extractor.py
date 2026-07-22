"""
Contract for extracting memories from raw input.
"""

from __future__ import annotations

from typing import Protocol

from app.cognition.memory.domain.entities import MemoryFact


class MemoryExtractor(Protocol):
    """
    Extracts memory facts from arbitrary input.
    """

    async def extract(
        self,
        content: str,
    ) -> tuple[MemoryFact, ...]:
        """
        Extract memory facts from text.
        """
        ...
