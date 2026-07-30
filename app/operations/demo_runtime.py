"""Controlled operational runtime for an explicit reasoning demonstration."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.engine import CognitiveEngine
from app.operations.provider_readiness import ProviderReadinessProbe

REASONING_DISABLED = "reasoning_disabled"
READINESS_FAILED = "readiness_failed"
COGNITIVE_SUCCEEDED = "cognitive_succeeded"
COGNITIVE_FAILED = "cognitive_failed"


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
