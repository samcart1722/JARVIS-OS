"""Infrastructure-independent processor contract for cognitive routing."""

from typing import Protocol

from app.cognition.domain.cognitive_outcome import CognitiveOutcome


class CognitiveProcessor(Protocol):
    def process(self, user_input: str) -> CognitiveOutcome: ...
