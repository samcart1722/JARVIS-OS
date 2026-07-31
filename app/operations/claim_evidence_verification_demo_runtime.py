"""Operational comparison of Sprint 18 attribution and Sprint 19 verification."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.provider_readiness import (
    ProviderReadinessProbe,
    ProviderReadinessResult,
)

VERIFICATION_COMPARISON_COMPLETED = "verification_comparison_completed"
VERIFICATION_COMPARISON_READINESS_FAILED = "readiness_failed"


@dataclass(frozen=True, slots=True)
class ClaimEvidenceVerificationDemoReport:
    status: str
    message: str
    readiness: ProviderReadinessResult
    claim_attributed_outcome: CognitiveOutcome | None
    verified_outcome: CognitiveOutcome | None
    record_count: int
    explicit_scope: bool

    def __post_init__(self) -> None:
        if self.record_count <= 0 or self.explicit_scope is not True:
            raise ValueError("Verification demo requires records and explicit scope.")
        both = (
            self.claim_attributed_outcome is not None
            and self.verified_outcome is not None
        )
        any_outcome = (
            self.claim_attributed_outcome is not None
            or self.verified_outcome is not None
        )
        if any_outcome != both or self.readiness.ready != both:
            raise ValueError("Readiness and verification demo outcomes must agree.")
        expected = (
            VERIFICATION_COMPARISON_COMPLETED
            if self.readiness.ready
            else VERIFICATION_COMPARISON_READINESS_FAILED
        )
        if self.status != expected:
            raise ValueError("Verification demo status does not match readiness.")


class ClaimEvidenceVerificationDemoRuntime:
    def __init__(
        self,
        *,
        readiness_probe: ProviderReadinessProbe,
        claim_attributed_engine: CognitiveEngine,
        verified_engine: CognitiveEngine,
        memory_scope: MemoryScope,
        record_count: int,
    ) -> None:
        if not isinstance(memory_scope, MemoryScope) or record_count <= 0:
            raise ValueError("Verification demo requires records and MemoryScope.")
        self._probe = readiness_probe
        self._claim_engine = claim_attributed_engine
        self._verified_engine = verified_engine
        self._scope = memory_scope
        self._record_count = record_count

    def run(self, prompt: str) -> ClaimEvidenceVerificationDemoReport:
        if not prompt.strip():
            raise ValueError("Demo prompt cannot be empty.")
        readiness = self._probe.check()
        if not readiness.ready:
            return ClaimEvidenceVerificationDemoReport(
                VERIFICATION_COMPARISON_READINESS_FAILED,
                f"{readiness.status}: {readiness.message}",
                readiness,
                None,
                None,
                self._record_count,
                True,
            )
        attributed = self._claim_engine.process(prompt, memory_scope=self._scope)
        verified = self._verified_engine.process(prompt, memory_scope=self._scope)
        return ClaimEvidenceVerificationDemoReport(
            VERIFICATION_COMPARISON_COMPLETED,
            "Both observational executions completed.",
            readiness,
            attributed,
            verified,
            self._record_count,
            True,
        )
