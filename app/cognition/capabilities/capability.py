"""Base contract for reusable cognitive capabilities."""

from abc import ABC, abstractmethod

from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.plan_step import PlanStep


class Capability(ABC):
    """Define a reusable core ability that executes a plan step."""

    @abstractmethod
    def execute(
        self,
        context: CognitiveContext,
        step: PlanStep,
    ) -> CapabilityResult:
        """Execute a plan step using cognitive context and return its result."""
