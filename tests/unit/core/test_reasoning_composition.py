"""Tests for reasoning composition without external calls."""

from unittest.mock import Mock

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.planning.goal import Goal
from app.cognition.specialists.default_specialist import DefaultSpecialist
from app.core.config import Settings
from app.core.container import Container


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
    plan = DefaultSpecialist().create_plan(Goal(description="Question"))

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
