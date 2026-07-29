"""Registry for logical capability identifiers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.cognition.capabilities.capability import Capability


class CapabilityAlreadyRegisteredError(ValueError):
    """Raised when a logical identifier is registered more than once."""


class CapabilityNotFoundError(LookupError):
    """Raised when no capability is registered for a logical identifier."""


class CapabilityRegistry:
    """Maintain the runtime mapping from identifiers to capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability_id: str, capability: Capability) -> None:
        """Register one capability under a unique logical identifier."""
        if capability_id in self._capabilities:
            raise CapabilityAlreadyRegisteredError(
                f"Capability already registered: {capability_id}"
            )
        self._capabilities[capability_id] = capability

    def get(self, capability_id: str) -> Capability:
        """Return the capability registered for the supplied identifier."""
        try:
            return self._capabilities[capability_id]
        except KeyError as error:
            raise CapabilityNotFoundError(
                f"Capability not registered: {capability_id}"
            ) from error
