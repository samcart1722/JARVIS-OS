"""
Value object representing the unique identifier of a MemoryFact.
"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class MemoryId:
    """
    Immutable identifier for a MemoryFact.
    """

    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)
