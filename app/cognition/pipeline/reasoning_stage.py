"""Reasoning stage for the cognitive pipeline."""


class ReasoningStage:
    """Produce the reasoning result from the prepared request context.

    Reasoning integrations are intentionally outside the scope of this cycle.
    """

    def process(self, context: str) -> str:
        """Return the context as the temporary reasoning result."""
        return context
