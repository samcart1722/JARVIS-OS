"""Input stage for the cognitive pipeline."""

from app.cognition.domain.cognitive_context import CognitiveContext


class InputStage:
    """Receive the user input and pass it into the cognitive pipeline."""

    def process(self, user_input: str) -> CognitiveContext:
        """Create the context that enters the cognitive pipeline."""
        return CognitiveContext(
            raw_input=user_input,
            normalized_input=user_input,
        )
