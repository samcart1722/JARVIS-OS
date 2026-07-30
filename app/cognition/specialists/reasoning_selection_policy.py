"""Contract for deterministic reasoning-capability selection."""

from typing import Protocol

from app.cognition.domain.cognitive_context import CognitiveContext


class ReasoningSelectionPolicy(Protocol):
    """Select the logical capability requested by the default specialist."""

    def select_capability(self, context: CognitiveContext) -> str:
        """Return one logical capability identifier for the supplied context."""
