"""Boolean-driven capability selection."""

from dataclasses import dataclass

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.specialists.reasoning_selection_policy import (
    ReasoningSelectionPolicy,
)


@dataclass(frozen=True)
class DeterministicReasoningSelectionPolicy(ReasoningSelectionPolicy):
    """Select a capability solely from immutable operational enablement."""

    reasoning_enabled: bool

    def select_capability(self, context: CognitiveContext) -> str:
        """Return reasoning when enabled, otherwise normalized input."""
        del context
        if self.reasoning_enabled:
            return REASONING_CAPABILITY_ID
        return NORMALIZED_INPUT_CAPABILITY_ID
