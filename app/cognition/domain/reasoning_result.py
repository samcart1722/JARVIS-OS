"""Domain result produced by the cognitive reasoning stage."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReasoningResult:
    """Represent the response produced by cognitive reasoning."""

    response: str
