"""Cognitive Engine entry point."""

from __future__ import annotations

from app.cognition.classification.goal_classifier import GoalClassifier
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.planning.goal import Goal
from app.cognition.specialists.specialist_router import SpecialistRouter


class CognitiveEngine:
    """Orchestrate cognitive flow through plan execution."""

    def __init__(
        self,
        goal_classifier: GoalClassifier,
        specialist_router: SpecialistRouter,
        capability_executor: CapabilityExecutor,
        response_stage: ResponseStage,
    ) -> None:
        self._goal_classifier = goal_classifier
        self._specialist_router = specialist_router
        self._capability_executor = capability_executor
        self._response_stage = response_stage

    def process(self, user_input: str) -> str:
        """Execute the selected specialist plan and return its public response."""
        goal = Goal(description=user_input)
        context = CognitiveContext(
            raw_input=user_input,
            normalized_input=user_input,
            goal=goal,
        )
        domain = self._goal_classifier.classify(context)
        specialist = self._specialist_router.route(domain)
        plan = specialist.create_plan(context)
        execution_result = self._capability_executor.execute(context, plan)

        return self._response_stage.process(execution_result)
