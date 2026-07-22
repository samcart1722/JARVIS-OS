"""
Value object representing the confidence assigned to a memory.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryConfidence:
    """
    Immutable confidence score for a MemoryFact.

    The value must always be between 0.0 and 1.0.
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Memory confidence must be between 0.0 and 1.0.")

    @property
    def percentage(self) -> float:
        """Return the confidence as a percentage."""
        return self.value * 100

    @property
    def is_high(self) -> bool:
        return self.value >= 0.80

    @property
    def is_medium(self) -> bool:
        return 0.50 <= self.value < 0.80

    @property
    def is_low(self) -> bool:
        return self.value < 0.50
