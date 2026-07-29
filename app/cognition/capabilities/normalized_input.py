"""Deterministic capability that exposes normalized request input."""

from app.cognition.capabilities.capability import Capability
from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.plan_step import PlanStep


class NormalizedInputCapability(Capability):
    """Return the normalized input already present in cognitive context."""

    def execute(
        self,
        context: CognitiveContext,
        step: PlanStep,
    ) -> CapabilityResult:
        """Produce normalized input without models or external services."""
        del step
        return CapabilityResult(
            success=True,
            outputs=(context.normalized_input,),
        )
