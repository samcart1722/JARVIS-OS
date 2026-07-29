"""Basic executor for high-level plans."""

from app.cognition.planning.execution_result import ExecutionResult
from app.cognition.planning.plan import Plan


class CapabilityExecutor:
    """Traverse plan steps without invoking external capabilities."""

    def __init__(self) -> None:
        self._executed_steps: list[str] = []

    def execute(self, plan: Plan) -> ExecutionResult:
        """Mark each plan step as executed and return its execution result."""
        self._executed_steps = []
        for step in plan.steps:
            self._executed_steps.append(step.description)

        return ExecutionResult(
            success=True,
            completed_steps=tuple(self._executed_steps),
        )
