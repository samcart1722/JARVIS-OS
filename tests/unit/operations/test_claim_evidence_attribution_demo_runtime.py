"""Claim attribution comparison runtime and report tests."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.claim_evidence_attribution_demo_runtime import (
    CLAIM_COMPARISON_COMPLETED,
    CLAIM_COMPARISON_READINESS_FAILED,
    ClaimEvidenceAttributionDemoReport,
    ClaimEvidenceAttributionDemoRuntime,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessProbe,
    readiness_result,
)


def outcome(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_report_is_immutable_safe_and_does_not_rank_results() -> None:
    report = ClaimEvidenceAttributionDemoReport(
        CLAIM_COMPARISON_COMPLETED,
        "Both observational executions completed.",
        readiness_result(READY),
        outcome("first"),
        outcome("second"),
        2,
        True,
    )
    assert "memory_scope" not in report.__dataclass_fields__
    assert "better" not in report.message.lower()
    assert "winner" not in report.message.lower()
    with pytest.raises(FrozenInstanceError):
        report.record_count = 3


def test_report_rejects_readiness_outcome_mismatch() -> None:
    with pytest.raises(ValueError, match="outcomes"):
        ClaimEvidenceAttributionDemoReport(
            CLAIM_COMPARISON_READINESS_FAILED,
            "invalid",
            readiness_result(PROVIDER_UNAVAILABLE),
            outcome("unexpected"),
            None,
            1,
            True,
        )


def test_runtime_is_inert_then_unready_checks_once_and_runs_zero_engines() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(PROVIDER_UNAVAILABLE)
    evidence = Mock(spec=CognitiveEngine)
    claim = Mock(spec=CognitiveEngine)
    runtime = ClaimEvidenceAttributionDemoRuntime(
        readiness_probe=probe,
        evidence_bounded_engine=evidence,
        claim_attributed_engine=claim,
        memory_scope=MemoryScope("hidden"),
        record_count=2,
    )
    probe.check.assert_not_called()
    report = runtime.run("same prompt")
    assert report.status == CLAIM_COMPARISON_READINESS_FAILED
    assert report.evidence_bounded_outcome is None
    assert report.claim_attributed_outcome is None
    probe.check.assert_called_once_with()
    evidence.process.assert_not_called()
    claim.process.assert_not_called()


def test_ready_runs_each_engine_once_with_same_prompt_scope_and_outcomes() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(READY)
    evidence = Mock(spec=CognitiveEngine)
    claim = Mock(spec=CognitiveEngine)
    first = outcome("first")
    second = outcome("second")
    evidence.process.return_value = first
    claim.process.return_value = second
    scope = MemoryScope("hidden")
    report = ClaimEvidenceAttributionDemoRuntime(
        readiness_probe=probe,
        evidence_bounded_engine=evidence,
        claim_attributed_engine=claim,
        memory_scope=scope,
        record_count=2,
    ).run("same prompt")
    assert report.evidence_bounded_outcome is first
    assert report.claim_attributed_outcome is second
    probe.check.assert_called_once_with()
    evidence.process.assert_called_once_with("same prompt", memory_scope=scope)
    claim.process.assert_called_once_with("same prompt", memory_scope=scope)


def test_blank_prompt_is_rejected_before_readiness() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    runtime = ClaimEvidenceAttributionDemoRuntime(
        readiness_probe=probe,
        evidence_bounded_engine=Mock(spec=CognitiveEngine),
        claim_attributed_engine=Mock(spec=CognitiveEngine),
        memory_scope=MemoryScope("hidden"),
        record_count=1,
    )
    with pytest.raises(ValueError, match="cannot be empty"):
        runtime.run(" ")
    probe.check.assert_not_called()
