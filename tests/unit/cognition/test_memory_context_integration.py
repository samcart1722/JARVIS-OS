"""Controlled tests for scoped memory propagation through the engine."""

from unittest.mock import Mock

import pytest

from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.capabilities.registry import CapabilityRegistry
from app.cognition.classification.goal_classifier import GoalClassifier
from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.domain.domain import Domain
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.contracts import MemoryContextRetriever
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.planning.plan import Plan
from app.cognition.planning.plan_step import PlanStep
from app.cognition.specialists.specialist_router import SpecialistRouter


def engine_with_mocks(
    *,
    enabled: bool,
    retriever: Mock | None,
) -> tuple[CognitiveEngine, Mock, Mock, Mock]:
    classifier = Mock(spec=GoalClassifier)
    classifier.classify.return_value = Domain.UNKNOWN
    specialist = Mock()
    specialist.create_plan.return_value = Plan(
        (PlanStep("step", "execute", "test"),)
    )
    router = Mock(spec=SpecialistRouter)
    router.route.return_value = specialist
    executor = Mock(spec=CapabilityExecutor)
    executor.execute.return_value = Mock(success=True, outputs=("output",))
    response = Mock(spec=ResponseStage)
    response.process.return_value = CognitiveOutcome(
        success=True, response="output"
    )
    engine = CognitiveEngine(
        classifier,
        router,
        executor,
        response,
        memory_context_retriever=retriever,
        memory_retrieval_enabled=enabled,
    )
    return engine, classifier, specialist, executor


def test_enabled_retrieval_requires_retriever_at_construction() -> None:
    with pytest.raises(ValueError, match="requires a context retriever"):
        engine_with_mocks(enabled=True, retriever=None)


@pytest.mark.parametrize(
    ("enabled", "scope"),
    (
        (False, None),
        (False, MemoryScope("scope-a")),
        (True, None),
    ),
)
def test_retrieval_does_not_run_unless_enabled_with_scope(
    enabled: bool, scope: MemoryScope | None
) -> None:
    retriever = Mock(spec=MemoryContextRetriever)
    engine, classifier, _, _ = engine_with_mocks(
        enabled=enabled, retriever=retriever
    )

    engine.process("Prompt", memory_scope=scope)

    retriever.retrieve.assert_not_called()
    assert classifier.classify.call_args.args[0].memory_snapshot is None


def test_retrieval_runs_before_classifier_and_propagates_same_context() -> None:
    scope = MemoryScope("scope-a")
    snapshot = MemorySnapshot(
        scope, (ScopedMemoryRecord(scope, "memory"),)
    )
    events: list[str] = []
    retriever = Mock(spec=MemoryContextRetriever)
    retriever.retrieve.side_effect = lambda scope, query: (
        events.append("retrieve") or snapshot
    )
    engine, classifier, specialist, executor = engine_with_mocks(
        enabled=True, retriever=retriever
    )
    classifier.classify.side_effect = lambda context: (
        events.append("classify") or Domain.UNKNOWN
    )

    engine.process("Normalized prompt", memory_scope=scope)

    assert events == ["retrieve", "classify"]
    retriever.retrieve.assert_called_once_with(scope, "Normalized prompt")
    context = classifier.classify.call_args.args[0]
    assert context.memory_snapshot is snapshot
    specialist.create_plan.assert_called_once_with(context)
    executor.execute.assert_called_once_with(
        context, specialist.create_plan.return_value
    )


def test_empty_snapshot_allows_execution() -> None:
    scope = MemoryScope("scope-a")
    retriever = Mock(spec=MemoryContextRetriever)
    retriever.retrieve.return_value = MemorySnapshot(scope)
    engine, classifier, _, _ = engine_with_mocks(
        enabled=True, retriever=retriever
    )

    outcome = engine.process("Prompt", memory_scope=scope)

    assert outcome.success is True
    assert classifier.classify.call_args.args[0].memory_snapshot.records == ()


def test_cross_scope_snapshot_is_rejected() -> None:
    requested = MemoryScope("scope-a")
    retriever = Mock(spec=MemoryContextRetriever)
    retriever.retrieve.return_value = MemorySnapshot(MemoryScope("scope-b"))
    engine, classifier, _, _ = engine_with_mocks(
        enabled=True, retriever=retriever
    )

    with pytest.raises(ValueError, match="does not match"):
        engine.process("Prompt", memory_scope=requested)

    classifier.classify.assert_not_called()


def test_retriever_error_propagates() -> None:
    retriever = Mock(spec=MemoryContextRetriever)
    retriever.retrieve.side_effect = RuntimeError("controlled retrieval error")
    engine, _, _, _ = engine_with_mocks(enabled=True, retriever=retriever)

    with pytest.raises(RuntimeError, match="controlled retrieval error"):
        engine.process("Prompt", memory_scope=MemoryScope("scope-a"))


def test_enriched_context_reaches_real_capability() -> None:
    scope = MemoryScope("scope-a")
    snapshot = MemorySnapshot(scope)
    retriever = Mock(spec=MemoryContextRetriever)
    retriever.retrieve.return_value = snapshot
    capability = Mock()
    capability.execute.return_value = CapabilityResult(
        success=True, outputs=("capability output",)
    )
    registry = CapabilityRegistry()
    registry.register("test", capability)
    classifier = Mock(spec=GoalClassifier)
    classifier.classify.return_value = Domain.UNKNOWN
    specialist = Mock()
    specialist.create_plan.return_value = Plan(
        (PlanStep("step", "execute", "test"),)
    )
    router = Mock(spec=SpecialistRouter)
    router.route.return_value = specialist
    engine = CognitiveEngine(
        classifier,
        router,
        CapabilityExecutor(registry),
        ResponseStage(),
        memory_context_retriever=retriever,
        memory_retrieval_enabled=True,
    )

    engine.process("Prompt", memory_scope=scope)

    assert capability.execute.call_args.args[0].memory_snapshot is snapshot


def test_enriched_context_reaches_controlled_reasoning_provider() -> None:
    scope = MemoryScope("scope-a")
    snapshot = MemorySnapshot(
        scope, (ScopedMemoryRecord(scope, "owned memory"),)
    )
    retriever = Mock(spec=MemoryContextRetriever)
    retriever.retrieve.return_value = snapshot
    provider = Mock()
    provider.generate.return_value = ReasoningResult("reasoned output")
    registry = CapabilityRegistry()
    registry.register(
        "reasoning",
        ReasoningCapability(ReasoningStage(provider)),
    )
    classifier = Mock(spec=GoalClassifier)
    classifier.classify.return_value = Domain.UNKNOWN
    specialist = Mock()
    specialist.create_plan.return_value = Plan(
        (PlanStep("step", "reason", "reasoning"),)
    )
    router = Mock(spec=SpecialistRouter)
    router.route.return_value = specialist
    engine = CognitiveEngine(
        classifier,
        router,
        CapabilityExecutor(registry),
        ResponseStage(),
        memory_context_retriever=retriever,
        memory_retrieval_enabled=True,
    )

    engine.process("Prompt", memory_scope=scope)

    observed_context = provider.generate.call_args.args[0]
    assert observed_context.memory_snapshot is snapshot
    assert observed_context.normalized_input == "Prompt"
