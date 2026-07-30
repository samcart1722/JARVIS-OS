"""Operational comparison of standard and evidence-bounded reasoning."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.provider_readiness import (
    ProviderReadinessProbe,
    ProviderReadinessResult,
)

GROUNDED_COMPARISON_COMPLETED = "grounded_comparison_completed"
GROUNDED_COMPARISON_READINESS_FAILED = "readiness_failed"


@dataclass(frozen=True)
class GroundedReasoningDemoReport:
    """Safe immutable standard-versus-grounded comparison report."""

    status: str
    message: str
    readiness: ProviderReadinessResult
    standard_outcome: CognitiveOutcome | None
    grounded_outcome: CognitiveOutcome | None
    record_count: int
    explicit_scope: bool

    def __post_init__(self) -> None:
        if self.record_count <= 0:
            raise ValueError("Grounded demo record count must be positive.")
        if self.explicit_scope is not True:
            raise ValueError("Grounded demo requires an explicit scope.")
        outcomes_present = (
            self.standard_outcome is not None
            and self.grounded_outcome is not None
        )
        any_outcome = (
            self.standard_outcome is not None
            or self.grounded_outcome is not None
        )
        if any_outcome and not outcomes_present:
            raise ValueError("Both grounded demo outcomes must be present.")
        if self.readiness.ready != outcomes_present:
            raise ValueError(
                "Readiness and grounded demo outcome presence must agree."
            )
        expected = (
            GROUNDED_COMPARISON_COMPLETED
            if self.readiness.ready
            else GROUNDED_COMPARISON_READINESS_FAILED
        )
        if self.status != expected:
            raise ValueError("Grounded demo status does not match readiness.")


class GroundedReasoningDemoRuntime:
    """Run one readiness check and both observational reasoning paths."""

    def __init__(
        self,
        *,
        readiness_probe: ProviderReadinessProbe,
        standard_engine: CognitiveEngine,
        grounded_engine: CognitiveEngine,
        memory_scope: MemoryScope,
        record_count: int,
    ) -> None:
        if not isinstance(memory_scope, MemoryScope):
            raise TypeError("Grounded demo requires a MemoryScope.")
        if record_count <= 0:
            raise ValueError("Grounded demo record count must be positive.")
        self._readiness_probe = readiness_probe
        self._standard_engine = standard_engine
        self._grounded_engine = grounded_engine
        self._memory_scope = memory_scope
        self._record_count = record_count

    def run(self, prompt: str) -> GroundedReasoningDemoReport:
        """Execute standard once and grounded once only when ready."""
        if not prompt.strip():
            raise ValueError("Demo prompt cannot be empty.")
        readiness = self._readiness_probe.check()
        if not readiness.ready:
            return GroundedReasoningDemoReport(
                status=GROUNDED_COMPARISON_READINESS_FAILED,
                message=f"{readiness.status}: {readiness.message}",
                readiness=readiness,
                standard_outcome=None,
                grounded_outcome=None,
                record_count=self._record_count,
                explicit_scope=True,
            )
        standard = self._standard_engine.process(
            prompt,
            memory_scope=self._memory_scope,
        )
        grounded = self._grounded_engine.process(
            prompt,
            memory_scope=self._memory_scope,
        )
        return GroundedReasoningDemoReport(
            status=GROUNDED_COMPARISON_COMPLETED,
            message="Standard and evidence-bounded executions completed.",
            readiness=readiness,
            standard_outcome=standard,
            grounded_outcome=grounded,
            record_count=self._record_count,
            explicit_scope=True,
        )
