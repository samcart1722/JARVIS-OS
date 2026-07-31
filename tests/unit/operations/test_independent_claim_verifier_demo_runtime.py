"""Independent verifier comparison runtime tests."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.independent_claim_verifier_demo_runtime import (
    INDEPENDENT_COMPARISON_COMPLETED,
    INDEPENDENT_COMPARISON_READINESS_FAILED,
    IndependentClaimVerifierDemoReport,
    IndependentClaimVerifierDemoRuntime,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessProbe,
    readiness_result,
)


def test_either_unready_checks_both_once_and_runs_zero_engines() -> None:
    for first_ready, second_ready in ((False, True), (True, False)):
        primary = Mock(spec=ProviderReadinessProbe)
        verifier = Mock(spec=ProviderReadinessProbe)
        primary.check.return_value = readiness_result(
            READY if first_ready else PROVIDER_UNAVAILABLE
        )
        verifier.check.return_value = readiness_result(
            READY if second_ready else PROVIDER_UNAVAILABLE
        )
        shared = Mock(spec=CognitiveEngine)
        independent = Mock(spec=CognitiveEngine)
        report = IndependentClaimVerifierDemoRuntime(
            primary_probe=primary,
            verifier_probe=verifier,
            shared_engine=shared,
            independent_engine=independent,
            memory_scope=MemoryScope("secret"),
            record_count=1,
        ).run("prompt")
        assert report.status == INDEPENDENT_COMPARISON_READINESS_FAILED
        primary.check.assert_called_once()
        verifier.check.assert_called_once()
        shared.process.assert_not_called()
        independent.process.assert_not_called()


def test_both_ready_run_each_engine_once_with_same_prompt_and_scope() -> None:
    primary = Mock(spec=ProviderReadinessProbe)
    verifier = Mock(spec=ProviderReadinessProbe)
    primary.check.return_value = verifier.check.return_value = readiness_result(READY)
    shared = Mock(spec=CognitiveEngine)
    independent = Mock(spec=CognitiveEngine)
    shared.process.return_value = CognitiveOutcome(success=True, response="shared")
    independent.process.return_value = CognitiveOutcome(
        success=True, response="independent"
    )
    scope = MemoryScope("secret")
    report = IndependentClaimVerifierDemoRuntime(
        primary_probe=primary,
        verifier_probe=verifier,
        shared_engine=shared,
        independent_engine=independent,
        memory_scope=scope,
        record_count=2,
    ).run("same")
    assert report.status == INDEPENDENT_COMPARISON_COMPLETED
    shared.process.assert_called_once_with("same", memory_scope=scope)
    independent.process.assert_called_once_with("same", memory_scope=scope)


def test_report_is_immutable_slotted_and_has_no_sensitive_fields() -> None:
    ready = readiness_result(READY)
    report = IndependentClaimVerifierDemoReport(
        INDEPENDENT_COMPARISON_COMPLETED,
        ready,
        ready,
        CognitiveOutcome(success=True, response="shared"),
        CognitiveOutcome(success=True, response="independent"),
        1,
        True,
    )
    assert "memory_scope" not in report.__dataclass_fields__
    assert "url" not in report.__dataclass_fields__
    assert "model" not in report.__dataclass_fields__
    with pytest.raises(FrozenInstanceError):
        report.record_count = 2


@pytest.mark.parametrize("status", ("unknown", ""))
def test_report_rejects_unknown_status(status: str) -> None:
    ready = readiness_result(READY)
    with pytest.raises(ValueError):
        IndependentClaimVerifierDemoReport(status, ready, ready, None, None, 1, True)


@pytest.mark.parametrize("count", (0, -1))
def test_report_rejects_invalid_record_count(count: int) -> None:
    ready = readiness_result(READY)
    with pytest.raises(ValueError):
        IndependentClaimVerifierDemoReport(
            INDEPENDENT_COMPARISON_COMPLETED,
            ready,
            ready,
            CognitiveOutcome(success=True, response="a"),
            CognitiveOutcome(success=True, response="b"),
            count,
            True,
        )


def test_report_rejects_scope_readiness_and_outcome_contradictions() -> None:
    ready = readiness_result(READY)
    unavailable = readiness_result(PROVIDER_UNAVAILABLE)
    outcome = CognitiveOutcome(success=True, response="safe")
    invalid = (
        (INDEPENDENT_COMPARISON_COMPLETED, ready, ready, outcome, outcome, 1, False),
        (
            INDEPENDENT_COMPARISON_COMPLETED,
            unavailable,
            ready,
            outcome,
            outcome,
            1,
            True,
        ),
        (INDEPENDENT_COMPARISON_COMPLETED, ready, ready, None, None, 1, True),
        (INDEPENDENT_COMPARISON_READINESS_FAILED, ready, ready, None, None, 1, True),
        (
            INDEPENDENT_COMPARISON_READINESS_FAILED,
            unavailable,
            ready,
            outcome,
            outcome,
            1,
            True,
        ),
        (INDEPENDENT_COMPARISON_COMPLETED, ready, ready, outcome, None, 1, True),
    )
    for values in invalid:
        with pytest.raises(ValueError):
            IndependentClaimVerifierDemoReport(*values)
