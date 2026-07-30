"""Tests for official Ollama operational settings."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings

OLLAMA_VARIABLES = (
    "OLLAMA_BASE_URL",
    "OLLAMA_MODELS_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TIMEOUT_SECONDS",
)
REASONING_VARIABLE = "REASONING_ENABLED"


def clear_ollama_environment(monkeypatch) -> None:
    for variable in OLLAMA_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def clear_reasoning_environment(monkeypatch) -> None:
    monkeypatch.delenv(REASONING_VARIABLE, raising=False)


def test_ollama_settings_preserve_previous_defaults(monkeypatch) -> None:
    clear_ollama_environment(monkeypatch)

    configured = Settings(_env_file=None)

    assert configured.OLLAMA_BASE_URL == (
        "http://localhost:11434/api/generate"
    )
    assert configured.OLLAMA_MODELS_URL == "http://localhost:11434/api/tags"
    assert configured.OLLAMA_MODEL == "llama3.2:3b"
    assert configured.OLLAMA_TIMEOUT_SECONDS == 120


@pytest.mark.parametrize(
    ("variable", "value", "attribute", "expected"),
    (
        (
            "OLLAMA_BASE_URL",
            "http://ollama.internal/api/generate",
            "OLLAMA_BASE_URL",
            "http://ollama.internal/api/generate",
        ),
        (
            "OLLAMA_MODELS_URL",
            "http://ollama.internal/api/tags",
            "OLLAMA_MODELS_URL",
            "http://ollama.internal/api/tags",
        ),
        ("OLLAMA_MODEL", "custom-model", "OLLAMA_MODEL", "custom-model"),
        ("OLLAMA_TIMEOUT_SECONDS", "45", "OLLAMA_TIMEOUT_SECONDS", 45),
    ),
)
def test_ollama_settings_support_environment_overrides(
    monkeypatch,
    variable: str,
    value: str,
    attribute: str,
    expected: str | int,
) -> None:
    clear_ollama_environment(monkeypatch)
    monkeypatch.setenv(variable, value)

    configured = Settings(_env_file=None)

    assert getattr(configured, attribute) == expected


@pytest.mark.parametrize("invalid_timeout", [0, -1])
def test_ollama_timeout_must_be_positive(
    monkeypatch,
    invalid_timeout: int,
) -> None:
    clear_ollama_environment(monkeypatch)
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", str(invalid_timeout))

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_instances_do_not_share_environment_state(monkeypatch) -> None:
    clear_ollama_environment(monkeypatch)
    monkeypatch.setenv("OLLAMA_MODEL", "first-model")
    first = Settings(_env_file=None)
    monkeypatch.setenv("OLLAMA_MODEL", "second-model")
    second = Settings(_env_file=None)

    assert first.OLLAMA_MODEL == "first-model"
    assert second.OLLAMA_MODEL == "second-model"


def test_reasoning_is_disabled_by_default_without_changing_ollama(
    monkeypatch,
) -> None:
    clear_reasoning_environment(monkeypatch)
    clear_ollama_environment(monkeypatch)

    configured = Settings(_env_file=None)

    assert configured.REASONING_ENABLED is False
    assert configured.OLLAMA_MODEL == "llama3.2:3b"
    assert configured.OLLAMA_TIMEOUT_SECONDS == 120


@pytest.mark.parametrize(
    ("environment_value", "expected"),
    (("true", True), ("false", False)),
)
def test_reasoning_supports_boolean_environment_override(
    monkeypatch,
    environment_value: str,
    expected: bool,
) -> None:
    clear_reasoning_environment(monkeypatch)
    monkeypatch.setenv(REASONING_VARIABLE, environment_value)

    configured = Settings(_env_file=None)

    assert configured.REASONING_ENABLED is expected


def test_invalid_reasoning_boolean_is_rejected(monkeypatch) -> None:
    clear_reasoning_environment(monkeypatch)
    monkeypatch.setenv(REASONING_VARIABLE, "sometimes")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_reasoning_setting_instances_are_independent(monkeypatch) -> None:
    clear_reasoning_environment(monkeypatch)
    monkeypatch.setenv(REASONING_VARIABLE, "true")
    enabled = Settings(_env_file=None)
    monkeypatch.setenv(REASONING_VARIABLE, "false")
    disabled = Settings(_env_file=None)

    assert enabled.REASONING_ENABLED is True
    assert disabled.REASONING_ENABLED is False


def test_env_example_contains_safe_reasoning_default() -> None:
    contents = Path(".env.example").read_text(encoding="utf-8")

    assert "REASONING_ENABLED=false" in contents
    assert "OLLAMA_MODELS_URL=http://localhost:11434/api/tags" in contents
