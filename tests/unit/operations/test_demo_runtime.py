"""Tests for the controlled reasoning demonstration runtime."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.demo_runtime import (
    COGNITIVE_FAILED,
    COGNITIVE_SUCCEEDED,
    COMPARISON_SUCCEEDED,
    READINESS_FAILED,
    REASONING_DISABLED,
    CognitiveDemoComparison,
    FunctionalCognitiveDemoRuntime,
    ReasoningDemoRuntime,
)
from app.operations.provider_readiness import (
    MODEL_UNAVAILABLE,
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessProbe,
    readiness_result,
)


@pytest.mark.parametrize(
    "readiness_status", (PROVIDER_UNAVAILABLE, MODEL_UNAVAILABLE)
)
def test_unready_provider_never_executes_engine(readiness_status: str) -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(readiness_status)
    engine = Mock(spec=CognitiveEngine)

    result = ReasoningDemoRuntime(
        reasoning_enabled=True,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == READINESS_FAILED
    assert readiness_status in result.message
    probe.check.assert_called_once_with()
    engine.process.assert_not_called()


def test_disabled_reasoning_performs_no_readiness_or_execution() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    engine = Mock(spec=CognitiveEngine)

    result = ReasoningDemoRuntime(
        reasoning_enabled=False,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == REASONING_DISABLED
    probe.check.assert_not_called()
    engine.process.assert_not_called()


def test_ready_provider_executes_engine_once_and_preserves_outcome() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result("ready")
    engine = Mock(spec=CognitiveEngine)
    outcome = CognitiveOutcome(success=True, response="Reasoned answer")
    engine.process.return_value = outcome

    result = ReasoningDemoRuntime(
        reasoning_enabled=True,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == COGNITIVE_SUCCEEDED
    assert result.cognitive_outcome is outcome
    assert result.message == "Reasoned answer"
    probe.check.assert_called_once_with()
    engine.process.assert_called_once_with("Prompt")


def test_cognitive_failure_remains_distinct_from_readiness_failure() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result("ready")
    engine = Mock(spec=CognitiveEngine)
    outcome = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_EXECUTION_FAILED),
    )
    engine.process.return_value = outcome

    result = ReasoningDemoRuntime(
        reasoning_enabled=True,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == COGNITIVE_FAILED
    assert result.cognitive_outcome is outcome
    assert CAPABILITY_EXECUTION_FAILED in result.message


def test_functional_demo_checks_readiness_once_and_runs_both_engines() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result("ready")
    baseline = Mock(spec=CognitiveEngine)
    memory = Mock(spec=CognitiveEngine)
    baseline_outcome = CognitiveOutcome(success=True, response="baseline")
    memory_outcome = CognitiveOutcome(success=True, response="memory")
    baseline.process.return_value = baseline_outcome
    memory.process.return_value = memory_outcome
    scope = MemoryScope("scope-a")

    result = FunctionalCognitiveDemoRuntime(
        readiness_probe=probe,
        baseline_engine=baseline,
        memory_engine=memory,
        memory_scope=scope,
        record_count=2,
    ).run("Prompt")

    assert result.status == COMPARISON_SUCCEEDED
    assert result.baseline_outcome is baseline_outcome
    assert result.memory_outcome is memory_outcome
    assert result.readiness.ready is True
    assert result.record_count == 2
    assert result.explicit_scope is True
    probe.check.assert_called_once_with()
    baseline.process.assert_called_once_with("Prompt")
    memory.process.assert_called_once_with("Prompt", memory_scope=scope)


@pytest.mark.parametrize(
    "status", (PROVIDER_UNAVAILABLE, MODEL_UNAVAILABLE)
)
def test_functional_demo_stops_both_engines_when_not_ready(status: str) -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(status)
    baseline = Mock(spec=CognitiveEngine)
    memory = Mock(spec=CognitiveEngine)

    result = FunctionalCognitiveDemoRuntime(
        readiness_probe=probe,
        baseline_engine=baseline,
        memory_engine=memory,
        memory_scope=MemoryScope("scope-a"),
        record_count=1,
    ).run("Prompt")

    assert result.status == READINESS_FAILED
    assert result.readiness.status == status
    assert result.record_count == 1
    assert result.explicit_scope is True
    assert result.baseline_outcome is None
    assert result.memory_outcome is None
    probe.check.assert_called_once_with()
    baseline.process.assert_not_called()
    memory.process.assert_not_called()


def test_functional_demo_preserves_structured_cognitive_failures() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result("ready")
    baseline = Mock(spec=CognitiveEngine)
    memory = Mock(spec=CognitiveEngine)
    failure = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_EXECUTION_FAILED),
    )
    baseline.process.return_value = failure
    memory.process.return_value = failure

    result = FunctionalCognitiveDemoRuntime(
        readiness_probe=probe,
        baseline_engine=baseline,
        memory_engine=memory,
        memory_scope=MemoryScope("scope-a"),
        record_count=1,
    ).run("Prompt")

    assert result.baseline_outcome is failure
    assert result.memory_outcome is failure


def test_functional_demo_rejects_empty_prompt_before_readiness() -> None:
    probe = Mock(spec=ProviderReadinessProbe)

    with pytest.raises(ValueError, match="cannot be empty"):
        FunctionalCognitiveDemoRuntime(
            readiness_probe=probe,
            baseline_engine=Mock(spec=CognitiveEngine),
            memory_engine=Mock(spec=CognitiveEngine),
            memory_scope=MemoryScope("scope-a"),
            record_count=1,
        ).run(" ")

    probe.check.assert_not_called()


def test_comparison_report_is_immutable_and_contains_no_scope() -> None:
    outcome = CognitiveOutcome(success=True, response="ok")
    report = CognitiveDemoComparison(
        status=COMPARISON_SUCCEEDED,
        message="complete",
        readiness=readiness_result(READY),
        record_count=1,
        explicit_scope=True,
        baseline_outcome=outcome,
        memory_outcome=outcome,
    )

    assert "memory_scope" not in report.__dataclass_fields__
    assert tuple(report.__dataclass_fields__) == (
        "status",
        "message",
        "readiness",
        "record_count",
        "explicit_scope",
        "baseline_outcome",
        "memory_outcome",
    )
    with pytest.raises(FrozenInstanceError):
        report.record_count = 2


def test_comparison_report_requires_positive_record_count() -> None:
    with pytest.raises(ValueError, match="positive"):
        CognitiveDemoComparison(
            status=READINESS_FAILED,
            message="not ready",
            readiness=readiness_result(PROVIDER_UNAVAILABLE),
            record_count=0,
            explicit_scope=True,
            baseline_outcome=None,
            memory_outcome=None,
        )


@pytest.mark.parametrize(
    ("readiness_status", "baseline", "memory"),
    (
        (
            READY,
            None,
            None,
        ),
        (
            PROVIDER_UNAVAILABLE,
            CognitiveOutcome(success=True, response="baseline"),
            CognitiveOutcome(success=True, response="memory"),
        ),
    ),
)
def test_comparison_report_enforces_readiness_outcome_invariant(
    readiness_status: str,
    baseline: CognitiveOutcome | None,
    memory: CognitiveOutcome | None,
) -> None:
    with pytest.raises(ValueError, match="presence must agree"):
        CognitiveDemoComparison(
            status=(
                COMPARISON_SUCCEEDED
                if readiness_status == READY
                else READINESS_FAILED
            ),
            message="safe",
            readiness=readiness_result(readiness_status),
            record_count=1,
            explicit_scope=True,
            baseline_outcome=baseline,
            memory_outcome=memory,
        )


def test_functional_demo_construction_has_no_side_effects() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    baseline = Mock(spec=CognitiveEngine)
    memory = Mock(spec=CognitiveEngine)

    FunctionalCognitiveDemoRuntime(
        readiness_probe=probe,
        baseline_engine=baseline,
        memory_engine=memory,
        memory_scope=MemoryScope("scope-a"),
        record_count=1,
    )

    probe.check.assert_not_called()
    baseline.process.assert_not_called()
    memory.process.assert_not_called()


def test_functional_demo_rejects_non_positive_record_count() -> None:
    with pytest.raises(ValueError, match="positive"):
        FunctionalCognitiveDemoRuntime(
            readiness_probe=Mock(spec=ProviderReadinessProbe),
            baseline_engine=Mock(spec=CognitiveEngine),
            memory_engine=Mock(spec=CognitiveEngine),
            memory_scope=MemoryScope("scope-a"),
            record_count=0,
        )
