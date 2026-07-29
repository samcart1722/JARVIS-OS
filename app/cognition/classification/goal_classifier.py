"""Cognitive context classification contract."""

from typing import Protocol

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.domain import Domain


class GoalClassifier(Protocol):
    """Define how a domain is classified from the full cognitive context."""

    def classify(self, context: CognitiveContext) -> Domain:
        """Classify the supplied cognitive context into a domain."""
