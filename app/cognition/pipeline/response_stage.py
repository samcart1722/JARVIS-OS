"""Response stage for the cognitive pipeline."""

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.planning.execution_result import ExecutionResult


class ResponseStage:
    """Convert an execution result into the public response."""

    def process(self, execution_result: ExecutionResult) -> CognitiveOutcome:
        """Translate execution state into a structured cognitive outcome."""
        if execution_result.success and execution_result.outputs:
            return CognitiveOutcome(
                success=True,
                response="\n".join(execution_result.outputs),
            )

        return CognitiveOutcome(
            success=False,
            error=cognitive_error(
                execution_result.error_code or CAPABILITY_EXECUTION_FAILED
            ),
        )
