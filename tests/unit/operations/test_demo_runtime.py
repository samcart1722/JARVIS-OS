"""Tests for the controlled reasoning demonstration runtime."""

from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.engine import CognitiveEngine
from app.operations.demo_runtime import (
    COGNITIVE_FAILED,
    COGNITIVE_SUCCEEDED,
    READINESS_FAILED,
    REASONING_DISABLED,
    ReasoningDemoRuntime,
)
from app.operations.provider_readiness import (
    MODEL_UNAVAILABLE,
    PROVIDER_UNAVAILABLE,
    ProviderReadinessProbe,
    readiness_result,
)


@pytest.mark.parametrize(
    "readiness_status", (PROVIDER_UNAVAILABLE, MODEL_UNAVAILABLE)
)
def test_unready_provider_never_executes_engine(readiness_status: str) -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(readiness_status)
    engine = Mock(spec=CognitiveEngine)

    result = ReasoningDemoRuntime(
        reasoning_enabled=True,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == READINESS_FAILED
    assert readiness_status in result.message
    probe.check.assert_called_once_with()
    engine.process.assert_not_called()


def test_disabled_reasoning_performs_no_readiness_or_execution() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    engine = Mock(spec=CognitiveEngine)

    result = ReasoningDemoRuntime(
        reasoning_enabled=False,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == REASONING_DISABLED
    probe.check.assert_not_called()
    engine.process.assert_not_called()


def test_ready_provider_executes_engine_once_and_preserves_outcome() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result("ready")
    engine = Mock(spec=CognitiveEngine)
    outcome = CognitiveOutcome(success=True, response="Reasoned answer")
    engine.process.return_value = outcome

    result = ReasoningDemoRuntime(
        reasoning_enabled=True,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == COGNITIVE_SUCCEEDED
    assert result.cognitive_outcome is outcome
    assert result.message == "Reasoned answer"
    probe.check.assert_called_once_with()
    engine.process.assert_called_once_with("Prompt")


def test_cognitive_failure_remains_distinct_from_readiness_failure() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result("ready")
    engine = Mock(spec=CognitiveEngine)
    outcome = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_EXECUTION_FAILED),
    )
    engine.process.return_value = outcome

    result = ReasoningDemoRuntime(
        reasoning_enabled=True,
        readiness_probe=probe,
        cognitive_engine=engine,
    ).run("Prompt")

    assert result.status == COGNITIVE_FAILED
    assert result.cognitive_outcome is outcome
    assert CAPABILITY_EXECUTION_FAILED in result.message

