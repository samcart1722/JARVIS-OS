"""Default specialist implementation."""

from app.cognition.capabilities.ids import NORMALIZED_INPUT_CAPABILITY_ID
from app.cognition.planning.goal import Goal
from app.cognition.planning.plan import Plan
from app.cognition.planning.plan_step import PlanStep
from app.cognition.specialists.specialist import Specialist


class DefaultSpecialist(Specialist):
    """Provide a minimum descriptive plan for any assigned goal."""

    def can_handle(self, goal: Goal) -> bool:
        """Accept any goal assigned to this default specialist."""
        del goal
        return True

    def create_plan(self, goal: Goal) -> Plan:
        """Create a one-step plan describing how to address the goal."""
        return Plan(
            steps=(
                PlanStep(
                    id="default-step-1",
                    description=f"Address the goal: {goal.description}",
                    capability_id=NORMALIZED_INPUT_CAPABILITY_ID,
                ),
            )
        )
