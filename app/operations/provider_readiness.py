"""Operational contract and safe result for provider readiness."""

from dataclasses import dataclass
from typing import Protocol

READY = "ready"
PROVIDER_UNAVAILABLE = "provider_unavailable"
MODEL_UNAVAILABLE = "model_unavailable"
INVALID_RESPONSE = "invalid_response"

_MESSAGES = {
    READY: "The reasoning provider and configured model are ready.",
    PROVIDER_UNAVAILABLE: "The reasoning provider is unavailable.",
    MODEL_UNAVAILABLE: "The configured reasoning model is unavailable.",
    INVALID_RESPONSE: "The reasoning provider returned an invalid response.",
}


@dataclass(frozen=True)
class ProviderReadinessResult:
    """Represent one immutable, provider-independent readiness result."""

    status: str
    ready: bool
    message: str

    def __post_init__(self) -> None:
        if self.status not in _MESSAGES:
            raise ValueError("Unknown provider readiness status.")
        if self.ready != (self.status == READY):
            raise ValueError("Readiness status and ready flag disagree.")
        if self.message != _MESSAGES[self.status]:
            raise ValueError("Readiness results require the canonical safe message.")


def readiness_result(status: str) -> ProviderReadinessResult:
    """Build a result containing only canonical, safe operational text."""
    try:
        message = _MESSAGES[status]
    except KeyError as error:
        raise ValueError("Unknown provider readiness status.") from error
    return ProviderReadinessResult(
        status=status,
        ready=status == READY,
        message=message,
    )


class ProviderReadinessProbe(Protocol):
    """Check provider readiness explicitly and without cognitive execution."""

    def check(self) -> ProviderReadinessResult:
        """Perform one on-demand readiness check."""
