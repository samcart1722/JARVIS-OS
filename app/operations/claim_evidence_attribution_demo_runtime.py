"""Operational comparison of Sprint 17 and claim-level attribution."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.provider_readiness import (
    ProviderReadinessProbe,
    ProviderReadinessResult,
)

CLAIM_COMPARISON_COMPLETED = "claim_comparison_completed"
CLAIM_COMPARISON_READINESS_FAILED = "readiness_failed"


@dataclass(frozen=True, slots=True)
class ClaimEvidenceAttributionDemoReport:
    status: str
    message: str
    readiness: ProviderReadinessResult
    evidence_bounded_outcome: CognitiveOutcome | None
    claim_attributed_outcome: CognitiveOutcome | None
    record_count: int
    explicit_scope: bool

    def __post_init__(self) -> None:
        if self.record_count <= 0 or self.explicit_scope is not True:
            raise ValueError("Claim demo requires records and explicit scope.")
        both = (
            self.evidence_bounded_outcome is not None
            and self.claim_attributed_outcome is not None
        )
        any_outcome = (
            self.evidence_bounded_outcome is not None
            or self.claim_attributed_outcome is not None
        )
        if any_outcome != both or self.readiness.ready != both:
            raise ValueError("Readiness and claim demo outcomes must agree.")
        expected = (
            CLAIM_COMPARISON_COMPLETED
            if self.readiness.ready
            else CLAIM_COMPARISON_READINESS_FAILED
        )
        if self.status != expected:
            raise ValueError("Claim demo status does not match readiness.")


class ClaimEvidenceAttributionDemoRuntime:
    def __init__(
        self,
        *,
        readiness_probe: ProviderReadinessProbe,
        evidence_bounded_engine: CognitiveEngine,
        claim_attributed_engine: CognitiveEngine,
        memory_scope: MemoryScope,
        record_count: int,
    ) -> None:
        if not isinstance(memory_scope, MemoryScope) or record_count <= 0:
            raise ValueError("Claim demo requires records and MemoryScope.")
        self._probe = readiness_probe
        self._evidence_engine = evidence_bounded_engine
        self._claim_engine = claim_attributed_engine
        self._scope = memory_scope
        self._record_count = record_count

    def run(self, prompt: str) -> ClaimEvidenceAttributionDemoReport:
        if not prompt.strip():
            raise ValueError("Demo prompt cannot be empty.")
        readiness = self._probe.check()
        if not readiness.ready:
            return ClaimEvidenceAttributionDemoReport(
                CLAIM_COMPARISON_READINESS_FAILED,
                f"{readiness.status}: {readiness.message}",
                readiness,
                None,
                None,
                self._record_count,
                True,
            )
        evidence = self._evidence_engine.process(prompt, memory_scope=self._scope)
        claim = self._claim_engine.process(prompt, memory_scope=self._scope)
        return ClaimEvidenceAttributionDemoReport(
            CLAIM_COMPARISON_COMPLETED,
            "Both observational executions completed.",
            readiness,
            evidence,
            claim,
            self._record_count,
            True,
        )
