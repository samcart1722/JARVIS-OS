"""Reasoning capability backed by the canonical reasoning stage."""

from app.cognition.capabilities.capability import Capability
from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import EMPTY_CAPABILITY_OUTPUT
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.planning.plan_step import PlanStep


class ReasoningCapability(Capability):
    """Expose provider-backed reasoning through the capability runtime."""

    def __init__(self, reasoning_stage: ReasoningStage) -> None:
        self._reasoning_stage = reasoning_stage

    def execute(
        self,
        context: CognitiveContext,
        step: PlanStep,
    ) -> CapabilityResult:
        """Run canonical reasoning once and translate its result."""
        del step
        result = self._reasoning_stage.process(context)
        if not result.response.strip():
            return CapabilityResult(
                success=False,
                errors=("Reasoning provider returned no output.",),
                error_code=EMPTY_CAPABILITY_OUTPUT,
            )

        return CapabilityResult(
            success=True,
            outputs=(result.response,),
        )
