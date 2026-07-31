"""Sprint 19 comparison runtime tests."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.claim_evidence_verification_demo_runtime import (
    VERIFICATION_COMPARISON_COMPLETED,
    VERIFICATION_COMPARISON_READINESS_FAILED,
    ClaimEvidenceVerificationDemoReport,
    ClaimEvidenceVerificationDemoRuntime,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessProbe,
    readiness_result,
)


def success(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_report_is_immutable_safe_and_observational() -> None:
    report = ClaimEvidenceVerificationDemoReport(
        VERIFICATION_COMPARISON_COMPLETED,
        "Both observational executions completed.",
        readiness_result(READY),
        success("18"),
        success("19"),
        2,
        True,
    )
    assert "memory_scope" not in report.__dataclass_fields__
    assert "better" not in report.message.lower()
    with pytest.raises(FrozenInstanceError):
        report.record_count = 1


def test_unready_checks_once_and_runs_zero_engines() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(PROVIDER_UNAVAILABLE)
    first = Mock(spec=CognitiveEngine)
    second = Mock(spec=CognitiveEngine)
    report = ClaimEvidenceVerificationDemoRuntime(
        readiness_probe=probe,
        claim_attributed_engine=first,
        verified_engine=second,
        memory_scope=MemoryScope("secret"),
        record_count=1,
    ).run("prompt")
    assert report.status == VERIFICATION_COMPARISON_READINESS_FAILED
    probe.check.assert_called_once()
    first.process.assert_not_called()
    second.process.assert_not_called()


def test_ready_runs_each_once_with_same_prompt_scope_and_preserves_outcomes() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(READY)
    first = Mock(spec=CognitiveEngine)
    second = Mock(spec=CognitiveEngine)
    first_result = success("18")
    second_result = success("19")
    first.process.return_value = first_result
    second.process.return_value = second_result
    scope = MemoryScope("secret")
    report = ClaimEvidenceVerificationDemoRuntime(
        readiness_probe=probe,
        claim_attributed_engine=first,
        verified_engine=second,
        memory_scope=scope,
        record_count=2,
    ).run("same")
    assert (
        report.claim_attributed_outcome is first_result
        and report.verified_outcome is second_result
    )
    probe.check.assert_called_once()
    first.process.assert_called_once_with("same", memory_scope=scope)
    second.process.assert_called_once_with("same", memory_scope=scope)
