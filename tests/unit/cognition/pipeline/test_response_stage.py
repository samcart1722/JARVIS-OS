"""Tests for structured response-stage outcomes."""

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CAPABILITY_NOT_FOUND,
)
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.planning.execution_result import ExecutionResult


def test_success_uses_real_execution_output() -> None:
    outcome = ResponseStage().process(
        ExecutionResult(
            success=True,
            completed_steps=("one", "two"),
            outputs=("First", "Second"),
        )
    )

    assert outcome.success is True
    assert outcome.response == "First\nSecond"
    assert outcome.error is None


def test_controlled_failure_has_no_cognitive_response() -> None:
    outcome = ResponseStage().process(
        ExecutionResult(
            success=False,
            completed_steps=(),
            errors=("internal raw detail",),
            error_code=CAPABILITY_NOT_FOUND,
        )
    )

    assert outcome.success is False
    assert outcome.response is None
    assert outcome.error is not None
    assert outcome.error.code == CAPABILITY_NOT_FOUND
    assert "internal raw detail" not in outcome.error.message
    assert outcome.response != "Plan execution failed."


def test_uncategorized_controlled_failure_uses_general_code() -> None:
    outcome = ResponseStage().process(
        ExecutionResult(
            success=False,
            completed_steps=(),
            errors=("legacy controlled detail",),
        )
    )

    assert outcome.error is not None
    assert outcome.error.code == CAPABILITY_EXECUTION_FAILED
