"""Controlled operational runtime for an explicit reasoning demonstration."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.provider_readiness import (
    ProviderReadinessProbe,
    ProviderReadinessResult,
)

REASONING_DISABLED = "reasoning_disabled"
READINESS_FAILED = "readiness_failed"
COGNITIVE_SUCCEEDED = "cognitive_succeeded"
COGNITIVE_FAILED = "cognitive_failed"
COMPARISON_SUCCEEDED = "comparison_succeeded"


@dataclass(frozen=True)
class DemoResult:
    """Safe, structured result from one demonstration run."""

    status: str
    message: str
    cognitive_outcome: CognitiveOutcome | None = None


class ReasoningDemoRuntime:
    """Gate one composed cognitive execution behind explicit readiness."""

    def __init__(
        self,
        *,
        reasoning_enabled: bool,
        readiness_probe: ProviderReadinessProbe,
        cognitive_engine: CognitiveEngine,
    ) -> None:
        self._reasoning_enabled = reasoning_enabled
        self._readiness_probe = readiness_probe
        self._cognitive_engine = cognitive_engine

    def run(self, prompt: str) -> DemoResult:
        """Run readiness once and cognitive execution only when ready."""
        if not self._reasoning_enabled:
            return DemoResult(
                status=REASONING_DISABLED,
                message=(
                    "Reasoning is disabled. Set REASONING_ENABLED=true "
                    "explicitly to run the demo."
                ),
            )

        readiness = self._readiness_probe.check()
        if not readiness.ready:
            return DemoResult(
                status=READINESS_FAILED,
                message=f"{readiness.status}: {readiness.message}",
            )

        outcome = self._cognitive_engine.process(prompt)
        if outcome.success:
            return DemoResult(
                status=COGNITIVE_SUCCEEDED,
                message=outcome.response or "",
                cognitive_outcome=outcome,
            )
        return DemoResult(
            status=COGNITIVE_FAILED,
            message=(
                f"{outcome.error.code}: {outcome.error.message}"
                if outcome.error
                else "Cognitive execution failed."
            ),
            cognitive_outcome=outcome,
        )


@dataclass(frozen=True)
class CognitiveDemoComparison:
    """Represent readiness or both visible cognitive demo outcomes."""

    status: str
    message: str
    readiness: ProviderReadinessResult
    record_count: int
    explicit_scope: bool
    baseline_outcome: CognitiveOutcome | None
    memory_outcome: CognitiveOutcome | None

    def __post_init__(self) -> None:
        if self.record_count <= 0:
            raise ValueError("Demo record count must be positive.")
        if self.explicit_scope is not True:
            raise ValueError("Functional demo requires an explicit scope.")
        outcomes_present = (
            self.baseline_outcome is not None
            and self.memory_outcome is not None
        )
        if self.readiness.ready != outcomes_present:
            raise ValueError(
                "Readiness and cognitive outcome presence must agree."
            )
        expected_status = (
            COMPARISON_SUCCEEDED if self.readiness.ready else READINESS_FAILED
        )
        if self.status != expected_status:
            raise ValueError("Comparison status does not match readiness.")


class FunctionalCognitiveDemoRuntime:
    """Run one readiness check followed by baseline and scoped-memory flows."""

    def __init__(
        self,
        *,
        readiness_probe: ProviderReadinessProbe,
        baseline_engine: CognitiveEngine,
        memory_engine: CognitiveEngine,
        memory_scope: MemoryScope,
        record_count: int,
    ) -> None:
        if record_count <= 0:
            raise ValueError("Demo record count must be positive.")
        self._readiness_probe = readiness_probe
        self._baseline_engine = baseline_engine
        self._memory_engine = memory_engine
        self._memory_scope = memory_scope
        self._record_count = record_count

    def run(self, prompt: str) -> CognitiveDemoComparison:
        """Compare two explicit reasoning executions when the provider is ready."""
        if not prompt.strip():
            raise ValueError("Demo prompt cannot be empty.")

        readiness = self._readiness_probe.check()
        if not readiness.ready:
            return CognitiveDemoComparison(
                status=READINESS_FAILED,
                message=f"{readiness.status}: {readiness.message}",
                readiness=readiness,
                record_count=self._record_count,
                explicit_scope=True,
                baseline_outcome=None,
                memory_outcome=None,
            )

        baseline = self._baseline_engine.process(prompt)
        memory = self._memory_engine.process(
            prompt,
            memory_scope=self._memory_scope,
        )
        return CognitiveDemoComparison(
            status=COMPARISON_SUCCEEDED,
            message="Baseline and memory-aware executions completed.",
            readiness=readiness,
            record_count=self._record_count,
            explicit_scope=True,
            baseline_outcome=baseline,
            memory_outcome=memory,
        )
