"""Tests for reasoning composition without external calls."""

from unittest.mock import Mock

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.domain import Domain
from app.cognition.planning.goal import Goal
from app.core.config import Settings
from app.core.container import Container


def context(prompt: str = "Question") -> CognitiveContext:
    goal = Goal(description=prompt)
    return CognitiveContext(
        raw_input=prompt,
        normalized_input=prompt,
        goal=goal,
    )


def test_container_registers_both_runtime_capabilities() -> None:
    container = Container()

    assert isinstance(
        container.capability_registry.get(NORMALIZED_INPUT_CAPABILITY_ID),
        NormalizedInputCapability,
    )
    assert isinstance(
        container.capability_registry.get(REASONING_CAPABILITY_ID),
        ReasoningCapability,
    )


def test_container_construction_does_not_call_ollama(monkeypatch) -> None:
    post = Mock()
    monkeypatch.setattr("app.models.ollama_client.requests.post", post)

    Container()

    post.assert_not_called()


def test_default_specialist_keeps_deterministic_capability_policy() -> None:
    container = Container(
        Settings(REASONING_ENABLED=False, _env_file=None)
    )
    specialist = container.specialist_router.route(Domain.UNKNOWN)
    plan = specialist.create_plan(context())

    assert len(plan.steps) == 1
    assert plan.steps[0].capability_id == NORMALIZED_INPUT_CAPABILITY_ID


def test_container_injects_official_settings_into_ollama_client() -> None:
    configured = Settings(
        OLLAMA_BASE_URL="http://configured.test/api/generate",
        OLLAMA_MODEL="configured-model",
        OLLAMA_TIMEOUT_SECONDS=30,
        _env_file=None,
    )

    container = Container(configured)

    assert container.ollama_client.url == (
        "http://configured.test/api/generate"
    )
    assert container.ollama_client.model == "configured-model"
    assert container.ollama_client.timeout_seconds == 30


def test_container_composes_reasoning_selection_from_settings() -> None:
    disabled = Container(
        Settings(REASONING_ENABLED=False, _env_file=None)
    )
    enabled = Container(Settings(REASONING_ENABLED=True, _env_file=None))

    assert disabled.reasoning_selection_policy.reasoning_enabled is False
    assert enabled.reasoning_selection_policy.reasoning_enabled is True
    assert (
        disabled.default_specialist.create_plan(context()).steps[0].capability_id
        == NORMALIZED_INPUT_CAPABILITY_ID
    )
    assert (
        enabled.default_specialist.create_plan(context()).steps[0].capability_id
        == REASONING_CAPABILITY_ID
    )


def test_enabled_reasoning_reaches_real_provider_output_without_network() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    container.ollama_client.chat = Mock(return_value="Controlled reasoning")

    response = container.cognitive_engine.process("Any prompt")

    assert response.success is True
    assert response.response == "Controlled reasoning"
    assert response.error is None
    container.ollama_client.chat.assert_called_once_with("Any prompt")


def test_enabled_reasoning_failure_has_no_normalized_input_fallback() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    container.ollama_client.chat = Mock(return_value="")

    response = container.cognitive_engine.process("Must not be fallback")

    assert response.success is False
    assert response.response is None
    assert response.error is not None
    assert response.error.code == "empty_capability_output"


def test_enabled_reasoning_exception_propagates_without_fallback() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    container.ollama_client.chat = Mock(
        side_effect=RuntimeError("controlled provider error")
    )

    import pytest

    with pytest.raises(RuntimeError, match="controlled provider error"):
        container.cognitive_engine.process("Must not be fallback")
