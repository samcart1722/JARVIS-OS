"""Tests for the structured final Cognitive Core outcome."""

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CAPABILITY_NOT_FOUND,
    COGNITIVE_ERROR_CODES,
    EMPTY_CAPABILITY_OUTPUT,
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
    CognitiveError,
    CognitiveOutcome,
    cognitive_error,
)


def test_valid_success_contains_a_non_empty_response() -> None:
    outcome = CognitiveOutcome(success=True, response="Useful response")

    assert outcome.response == "Useful response"
    assert outcome.error is None


def test_valid_failure_contains_a_structured_error() -> None:
    error = cognitive_error(CAPABILITY_EXECUTION_FAILED)

    outcome = CognitiveOutcome(success=False, error=error)

    assert outcome.response is None
    assert outcome.error is error


@pytest.mark.parametrize(
    ("success", "response", "error"),
    [
        (
            True,
            "response",
            CognitiveError(code="conflict", message="conflict"),
        ),
        (True, None, None),
        (True, " \n", None),
        (False, None, None),
        (
            False,
            "invalid response",
            CognitiveError(code="failure", message="failure"),
        ),
    ],
)
def test_invalid_outcome_states_are_rejected(
    success: bool,
    response: str | None,
    error: CognitiveError | None,
) -> None:
    with pytest.raises(ValueError):
        CognitiveOutcome(success=success, response=response, error=error)


def test_error_codes_are_centralized_and_infrastructure_neutral() -> None:
    assert COGNITIVE_ERROR_CODES == {
        CAPABILITY_NOT_FOUND,
        CAPABILITY_EXECUTION_FAILED,
        EMPTY_CAPABILITY_OUTPUT,
        GROUNDED_RESPONSE_PROTOCOL_INVALID,
    }
    joined = " ".join(COGNITIVE_ERROR_CODES).lower()
    assert "ollama" not in joined
    assert "provider" not in joined
    assert "http" not in joined
    assert "url" not in joined
