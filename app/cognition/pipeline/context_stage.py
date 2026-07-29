"""Context stage for the cognitive pipeline."""


class ContextStage:
    """Prepare the currently available context for the request.

    This first cycle has no context providers, so the request is forwarded
    unchanged.
    """

    def process(self, user_input: str) -> str:
        """Return the request with the currently available context."""
        return user_input
