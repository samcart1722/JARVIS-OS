"""Reasoning stage for the cognitive pipeline."""

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.providers.base_provider import ReasoningProvider


class ReasoningStage:
    """Produce the reasoning result from the prepared request context.

    The concrete reasoning implementation is supplied through a provider.
    """

    def __init__(self, provider: ReasoningProvider) -> None:
        self._provider = provider

    def process(self, context: CognitiveContext) -> ReasoningResult:
        """Generate the result using the configured reasoning provider."""
        return self._provider.generate(context)
