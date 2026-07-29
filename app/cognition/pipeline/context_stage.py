"""Context stage for the cognitive pipeline."""

from app.cognition.domain.cognitive_context import CognitiveContext


class ContextStage:
    """Prepare the currently available context for the request.

    This first cycle has no context providers, so the request is forwarded
    unchanged.
    """

    def process(self, context: CognitiveContext) -> CognitiveContext:
        """Return the context without adding external information."""
        return context
