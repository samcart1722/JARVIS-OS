"""Input stage for the cognitive pipeline."""


class InputStage:
    """Receive the user input and pass it into the cognitive pipeline."""

    def process(self, user_input: str) -> str:
        """Return the user input without applying cognitive processing."""
        return user_input
