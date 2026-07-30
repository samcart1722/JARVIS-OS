"""Structured final outcome produced by the Cognitive Core."""

from dataclasses import dataclass

CAPABILITY_NOT_FOUND = "capability_not_found"
CAPABILITY_EXECUTION_FAILED = "capability_execution_failed"
EMPTY_CAPABILITY_OUTPUT = "empty_capability_output"

COGNITIVE_ERROR_CODES = frozenset(
    {
        CAPABILITY_NOT_FOUND,
        CAPABILITY_EXECUTION_FAILED,
        EMPTY_CAPABILITY_OUTPUT,
    }
)

_ERROR_MESSAGES = {
    CAPABILITY_NOT_FOUND: "The requested cognitive capability is unavailable.",
    CAPABILITY_EXECUTION_FAILED: (
        "The requested cognitive capability could not complete."
    ),
    EMPTY_CAPABILITY_OUTPUT: (
        "The requested cognitive capability produced no usable result."
    ),
}


@dataclass(frozen=True)
class CognitiveError:
    """Represent a stable, provider-independent cognitive failure."""

    code: str
    message: str


@dataclass(frozen=True)
class CognitiveOutcome:
    """Represent either a usable cognitive response or a controlled failure."""

    success: bool
    response: str | None = None
    error: CognitiveError | None = None

    def __post_init__(self) -> None:
        if self.success:
            if self.error is not None:
                raise ValueError("A successful outcome cannot contain an error.")
            if self.response is None or not self.response.strip():
                raise ValueError(
                    "A successful outcome requires a non-empty response."
                )
            return

        if self.error is None:
            raise ValueError("A failed outcome requires an error.")
        if self.response is not None:
            raise ValueError("A failed outcome cannot contain a response.")


def cognitive_error(code: str) -> CognitiveError:
    """Build the canonical safe error for a known cognitive failure code."""
    try:
        message = _ERROR_MESSAGES[code]
    except KeyError as error:
        raise ValueError(f"Unknown cognitive error code: {code}") from error
    return CognitiveError(code=code, message=message)
