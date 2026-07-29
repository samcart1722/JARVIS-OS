"""Tests for official Ollama operational settings."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

OLLAMA_VARIABLES = (
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TIMEOUT_SECONDS",
)


def clear_ollama_environment(monkeypatch) -> None:
    for variable in OLLAMA_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_ollama_settings_preserve_previous_defaults(monkeypatch) -> None:
    clear_ollama_environment(monkeypatch)

    configured = Settings(_env_file=None)

    assert configured.OLLAMA_BASE_URL == (
        "http://localhost:11434/api/generate"
    )
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
