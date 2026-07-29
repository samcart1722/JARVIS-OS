"""Response stage for the cognitive pipeline."""

from app.cognition.planning.execution_result import ExecutionResult


class ResponseStage:
    """Convert an execution result into the public response."""

    def process(self, execution_result: ExecutionResult) -> str:
        """Return the minimal public representation of an execution result."""
        if execution_result.success and execution_result.outputs:
            return "\n".join(execution_result.outputs)

        if execution_result.success:
            return "Plan executed successfully."

        return "Plan execution failed."
