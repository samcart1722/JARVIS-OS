"""Default specialist implementation."""

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.goal import Goal
from app.cognition.planning.plan import Plan
from app.cognition.planning.plan_step import PlanStep
from app.cognition.specialists.reasoning_selection_policy import (
    ReasoningSelectionPolicy,
)
from app.cognition.specialists.specialist import Specialist


class DefaultSpecialist(Specialist):
    """Provide a minimum descriptive plan for any assigned goal."""

    def __init__(self, selection_policy: ReasoningSelectionPolicy) -> None:
        self._selection_policy = selection_policy

    def can_handle(self, goal: Goal) -> bool:
        """Accept any goal assigned to this default specialist."""
        del goal
        return True

    def create_plan(self, context: CognitiveContext) -> Plan:
        """Create a one-step plan describing how to address the goal."""
        capability_id = self._selection_policy.select_capability(context)
        description = context.normalized_input
        if context.goal is not None:
            description = context.goal.description

        return Plan(
            steps=(
                PlanStep(
                    id="default-step-1",
                    description=f"Address the goal: {description}",
                    capability_id=capability_id,
                ),
            )
        )
