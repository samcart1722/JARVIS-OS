"""Tests for the grounded comparison runtime and immutable report."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import (
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.grounded_reasoning_demo_runtime import (
    GROUNDED_COMPARISON_COMPLETED,
    GROUNDED_COMPARISON_READINESS_FAILED,
    GroundedReasoningDemoReport,
    GroundedReasoningDemoRuntime,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessProbe,
    readiness_result,
)


def success(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_report_is_immutable_contains_no_scope_and_preserves_failure() -> None:
    failure = CognitiveOutcome(
        success=False,
        error=cognitive_error(GROUNDED_RESPONSE_PROTOCOL_INVALID),
    )
    report = GroundedReasoningDemoReport(
        status=GROUNDED_COMPARISON_COMPLETED,
        message="complete",
        readiness=readiness_result(READY),
        standard_outcome=success("standard"),
        grounded_outcome=failure,
        record_count=2,
        explicit_scope=True,
    )

    assert report.grounded_outcome is failure
    assert "memory_scope" not in report.__dataclass_fields__
    with pytest.raises(FrozenInstanceError):
        report.record_count = 1


def test_report_enforces_readiness_outcome_invariant() -> None:
    with pytest.raises(ValueError, match="Both grounded demo outcomes"):
        GroundedReasoningDemoReport(
            status=GROUNDED_COMPARISON_READINESS_FAILED,
            message="invalid",
            readiness=readiness_result(PROVIDER_UNAVAILABLE),
            standard_outcome=success("unexpected"),
            grounded_outcome=None,
            record_count=1,
            explicit_scope=True,
        )


def test_runtime_construction_has_no_effects() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    standard = Mock(spec=CognitiveEngine)
    grounded = Mock(spec=CognitiveEngine)

    GroundedReasoningDemoRuntime(
        readiness_probe=probe,
        standard_engine=standard,
        grounded_engine=grounded,
        memory_scope=MemoryScope("scope-a"),
        record_count=1,
    )

    probe.check.assert_not_called()
    standard.process.assert_not_called()
    grounded.process.assert_not_called()


def test_unready_checks_once_and_executes_zero_engines() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(PROVIDER_UNAVAILABLE)
    standard = Mock(spec=CognitiveEngine)
    grounded = Mock(spec=CognitiveEngine)

    report = GroundedReasoningDemoRuntime(
        readiness_probe=probe,
        standard_engine=standard,
        grounded_engine=grounded,
        memory_scope=MemoryScope("scope-a"),
        record_count=2,
    ).run("Exact prompt")

    assert report.status == GROUNDED_COMPARISON_READINESS_FAILED
    assert report.standard_outcome is None
    assert report.grounded_outcome is None
    probe.check.assert_called_once_with()
    standard.process.assert_not_called()
    grounded.process.assert_not_called()


def test_ready_runs_each_engine_once_with_same_prompt_and_scope() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(READY)
    standard = Mock(spec=CognitiveEngine)
    grounded = Mock(spec=CognitiveEngine)
    standard_result = success("standard")
    grounded_result = success("grounded")
    standard.process.return_value = standard_result
    grounded.process.return_value = grounded_result
    scope = MemoryScope("scope-a")

    report = GroundedReasoningDemoRuntime(
        readiness_probe=probe,
        standard_engine=standard,
        grounded_engine=grounded,
        memory_scope=scope,
        record_count=2,
    ).run("Exact prompt")

    assert report.status == GROUNDED_COMPARISON_COMPLETED
    assert report.standard_outcome is standard_result
    assert report.grounded_outcome is grounded_result
    probe.check.assert_called_once_with()
    standard.process.assert_called_once_with(
        "Exact prompt",
        memory_scope=scope,
    )
    grounded.process.assert_called_once_with(
        "Exact prompt",
        memory_scope=scope,
    )


def test_empty_prompt_is_rejected_before_readiness() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    runtime = GroundedReasoningDemoRuntime(
        readiness_probe=probe,
        standard_engine=Mock(spec=CognitiveEngine),
        grounded_engine=Mock(spec=CognitiveEngine),
        memory_scope=MemoryScope("scope-a"),
        record_count=1,
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        runtime.run(" ")
    probe.check.assert_not_called()
