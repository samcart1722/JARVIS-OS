"""Operational comparison of shared and independent verifier clients."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.provider_readiness import (
    ProviderReadinessProbe,
    ProviderReadinessResult,
)

INDEPENDENT_COMPARISON_COMPLETED = "independent_comparison_completed"
INDEPENDENT_COMPARISON_READINESS_FAILED = "readiness_failed"


@dataclass(frozen=True, slots=True)
class IndependentClaimVerifierDemoReport:
    status: str
    primary_readiness: ProviderReadinessResult
    verifier_readiness: ProviderReadinessResult
    shared_outcome: CognitiveOutcome | None
    independent_outcome: CognitiveOutcome | None
    record_count: int
    explicit_scope: bool

    def __post_init__(self) -> None:
        if self.status not in (
            INDEPENDENT_COMPARISON_COMPLETED,
            INDEPENDENT_COMPARISON_READINESS_FAILED,
        ):
            raise ValueError("Unknown independent demo status.")
        if self.record_count <= 0:
            raise ValueError("Independent demo record count must be positive.")
        if self.explicit_scope is not True:
            raise ValueError("Independent demo requires explicit scope.")
        both_outcomes = (
            self.shared_outcome is not None and self.independent_outcome is not None
        )
        any_outcome = (
            self.shared_outcome is not None or self.independent_outcome is not None
        )
        if any_outcome and not both_outcomes:
            raise ValueError("Independent demo requires both outcomes.")
        if self.status == INDEPENDENT_COMPARISON_COMPLETED:
            if (
                not self.primary_readiness.ready
                or not self.verifier_readiness.ready
                or not both_outcomes
            ):
                raise ValueError("Completed independent demo is inconsistent.")
        elif (
            self.primary_readiness.ready and self.verifier_readiness.ready
        ) or any_outcome:
            raise ValueError("Failed-readiness independent demo is inconsistent.")


class IndependentClaimVerifierDemoRuntime:
    def __init__(
        self,
        *,
        primary_probe: ProviderReadinessProbe,
        verifier_probe: ProviderReadinessProbe,
        shared_engine: CognitiveEngine,
        independent_engine: CognitiveEngine,
        memory_scope: MemoryScope,
        record_count: int,
    ) -> None:
        if not isinstance(memory_scope, MemoryScope) or record_count <= 0:
            raise ValueError("Independent demo requires records and MemoryScope.")
        self._primary_probe = primary_probe
        self._verifier_probe = verifier_probe
        self._shared_engine = shared_engine
        self._independent_engine = independent_engine
        self._scope = memory_scope
        self._record_count = record_count

    def run(self, prompt: str) -> IndependentClaimVerifierDemoReport:
        if not prompt.strip():
            raise ValueError("Demo prompt cannot be empty.")
        primary = self._primary_probe.check()
        verifier = self._verifier_probe.check()
        if not primary.ready or not verifier.ready:
            return IndependentClaimVerifierDemoReport(
                INDEPENDENT_COMPARISON_READINESS_FAILED,
                primary,
                verifier,
                None,
                None,
                self._record_count,
                True,
            )
        shared = self._shared_engine.process(prompt, memory_scope=self._scope)
        independent = self._independent_engine.process(prompt, memory_scope=self._scope)
        return IndependentClaimVerifierDemoReport(
            INDEPENDENT_COMPARISON_COMPLETED,
            primary,
            verifier,
            shared,
            independent,
            self._record_count,
            True,
        )
