"""Domain context shared by the cognitive pipeline stages."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitiveContext:
    """Represent the original input and its normalized form."""

    raw_input: str
    normalized_input: str
