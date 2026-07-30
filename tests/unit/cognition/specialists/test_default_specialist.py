"""Tests for policy-driven DefaultSpecialist planning."""

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.goal import Goal
from app.cognition.specialists.default_specialist import DefaultSpecialist


class SelectionPolicySpy:
    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.contexts: list[CognitiveContext] = []

    def select_capability(self, context: CognitiveContext) -> str:
        self.contexts.append(context)
        return self.capability_id


def test_specialist_delegates_once_and_preserves_plan_structure() -> None:
    policy = SelectionPolicySpy("selected-by-policy")
    specialist = DefaultSpecialist(policy)
    goal = Goal(description="Prepare a monthly order")
    context = CognitiveContext(
        raw_input=goal.description,
        normalized_input=goal.description,
        goal=goal,
    )

    plan = specialist.create_plan(context)

    assert policy.contexts == [context]
    assert context.goal is goal
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "default-step-1"
    assert plan.steps[0].description == (
        "Address the goal: Prepare a monthly order"
    )
    assert plan.steps[0].capability_id == "selected-by-policy"
