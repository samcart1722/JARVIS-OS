"""Base abstraction for cognitive reasoning providers."""

from typing import Protocol

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult


class ReasoningProvider(Protocol):
    """Define the contract for a provider that generates reasoning results."""

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        """Generate a reasoning result from the supplied cognitive context."""
