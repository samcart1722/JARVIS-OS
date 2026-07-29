"""Response stage for the cognitive pipeline."""

from app.cognition.domain.reasoning_result import ReasoningResult


class ResponseStage:
    """Convert the reasoning result into the current public response."""

    def process(self, reasoning_result: ReasoningResult) -> str:
        """Return the response produced by the reasoning stage."""
        return reasoning_result.response
