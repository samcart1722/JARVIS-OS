"""Default GoalClassifier implementation."""

from app.cognition.classification.goal_classifier import GoalClassifier
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.domain import Domain


class DefaultGoalClassifier(GoalClassifier):
    """Classify unrecognized cognitive contexts into the fallback domain."""

    def classify(self, context: CognitiveContext) -> Domain:
        """Return the fallback domain until classification policies are added."""
        del context
        return Domain.UNKNOWN
