"""Response stage for the cognitive pipeline."""


class ResponseStage:
    """Convert the reasoning result into the current public response."""

    def process(self, reasoning_result: str) -> str:
        """Return the temporary response while response generation is pending."""
        del reasoning_result
        return "El Cognitive Engine está en migración."
