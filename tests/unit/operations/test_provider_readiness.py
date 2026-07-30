"""Tests for the safe operational readiness result."""

from dataclasses import FrozenInstanceError

import pytest

from app.operations.provider_readiness import (
    MODEL_UNAVAILABLE,
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessResult,
    readiness_result,
)


@pytest.mark.parametrize(
    ("status", "ready"),
    (
        (READY, True),
        (PROVIDER_UNAVAILABLE, False),
        (MODEL_UNAVAILABLE, False),
    ),
)
def test_result_represents_canonical_states(status: str, ready: bool) -> None:
    result = readiness_result(status)

    assert result.status == status
    assert result.ready is ready
    assert "Traceback" not in result.message
    assert "C:\\" not in result.message
    assert "http://" not in result.message


def test_result_rejects_contradictory_state() -> None:
    with pytest.raises(ValueError):
        ProviderReadinessResult(
            status=READY,
            ready=False,
            message="The reasoning provider and configured model are ready.",
        )


def test_result_is_immutable() -> None:
    result = readiness_result(READY)

    with pytest.raises(FrozenInstanceError):
        result.ready = False  # type: ignore[misc]
