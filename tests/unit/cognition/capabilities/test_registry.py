"""Tests for the direct capability registry."""

import pytest

from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.capabilities.registry import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotFoundError,
    CapabilityRegistry,
)


def test_registry_registers_and_resolves_a_capability() -> None:
    registry = CapabilityRegistry()
    capability = NormalizedInputCapability()

    registry.register("normalized_input", capability)

    assert registry.get("normalized_input") is capability


def test_registry_rejects_duplicate_identifiers() -> None:
    registry = CapabilityRegistry()
    registry.register("normalized_input", NormalizedInputCapability())

    with pytest.raises(CapabilityAlreadyRegisteredError):
        registry.register("normalized_input", NormalizedInputCapability())


def test_registry_reports_a_missing_capability() -> None:
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotFoundError):
        registry.get("missing")
