"""Sequential executor for registered cognitive capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.cognition.capabilities.registry import (
    CapabilityNotFoundError,
    CapabilityRegistry,
)
from app.cognition.planning.execution_result import ExecutionResult
from app.cognition.planning.plan import Plan

if TYPE_CHECKING:
    from app.cognition.domain.cognitive_context import CognitiveContext


class CapabilityExecutor:
    """Execute registered capabilities sequentially with fail-fast semantics."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        context: CognitiveContext,
        plan: Plan,
    ) -> ExecutionResult:
        """Execute plan steps in order and aggregate successful results."""
        completed_steps: list[str] = []
        outputs: list[str] = []
        metadata: list[dict[str, object]] = []
        for step in plan.steps:
            try:
                capability = self._registry.get(step.capability_id)
            except CapabilityNotFoundError:
                return ExecutionResult(
                    success=False,
                    completed_steps=tuple(completed_steps),
                    outputs=tuple(outputs),
                    errors=(
                        f"Capability is not available: {step.capability_id}",
                    ),
                    metadata=tuple(metadata),
                )

            result = capability.execute(context, step)
            metadata.append(dict(result.metadata))
            if not result.success:
                return ExecutionResult(
                    success=False,
                    completed_steps=tuple(completed_steps),
                    outputs=tuple(outputs),
                    errors=result.errors,
                    metadata=tuple(metadata),
                )

            completed_steps.append(step.description)
            outputs.extend(result.outputs)

        # An empty plan is a valid execution with no completed work or output.
        return ExecutionResult(
            success=True,
            completed_steps=tuple(completed_steps),
            outputs=tuple(outputs),
            metadata=tuple(metadata),
        )
