"""Cognitive Engine entry point."""

from __future__ import annotations

from dataclasses import replace

from app.cognition.classification.goal_classifier import GoalClassifier
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.memory.scoped.contracts import MemoryContextRetriever
from app.cognition.memory.scoped.models import MemoryScope
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
        *,
        memory_context_retriever: MemoryContextRetriever | None = None,
        memory_retrieval_enabled: bool = False,
    ) -> None:
        if memory_retrieval_enabled and memory_context_retriever is None:
            raise ValueError(
                "Enabled memory retrieval requires a context retriever."
            )
        self._goal_classifier = goal_classifier
        self._specialist_router = specialist_router
        self._capability_executor = capability_executor
        self._response_stage = response_stage
        self._memory_context_retriever = memory_context_retriever
        self._memory_retrieval_enabled = memory_retrieval_enabled

    def process(
        self,
        user_input: str,
        *,
        memory_scope: MemoryScope | None = None,
    ) -> CognitiveOutcome:
        """Execute a specialist plan and return its structured outcome."""
        goal = Goal(description=user_input)
        context = CognitiveContext(
            raw_input=user_input,
            normalized_input=user_input,
            goal=goal,
        )
        if self._memory_retrieval_enabled and memory_scope is not None:
            if self._memory_context_retriever is None:
                raise RuntimeError("Memory retriever composition is invalid.")
            snapshot = self._memory_context_retriever.retrieve(
                memory_scope,
                context.normalized_input,
            )
            if snapshot.scope != memory_scope:
                raise ValueError(
                    "Retrieved memory snapshot does not match requested scope."
                )
            context = replace(context, memory_snapshot=snapshot)
        domain = self._goal_classifier.classify(context)
        specialist = self._specialist_router.route(domain)
        plan = specialist.create_plan(context)
        execution_result = self._capability_executor.execute(context, plan)

        return self._response_stage.process(execution_result)
