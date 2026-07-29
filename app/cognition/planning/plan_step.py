"""High-level plan step model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanStep:
    """Represent one descriptive step in a high-level plan."""

    id: str
    description: str
    capability_id: str = ""
