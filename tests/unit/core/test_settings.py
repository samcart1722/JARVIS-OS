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
MEMORY_RETRIEVAL_VARIABLE = "MEMORY_RETRIEVAL_ENABLED"
MEMORY_UPDATE_VARIABLE = "MEMORY_UPDATE_ENABLED"
MEMORY_PROMPT_VARIABLES = (
    "MEMORY_PROMPT_CONTEXT_ENABLED",
    "MEMORY_PROMPT_MAX_RECORDS",
    "MEMORY_PROMPT_MAX_CHARACTERS",
)


def clear_ollama_environment(monkeypatch) -> None:
    for variable in OLLAMA_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def clear_reasoning_environment(monkeypatch) -> None:
    monkeypatch.delenv(REASONING_VARIABLE, raising=False)


def clear_memory_retrieval_environment(monkeypatch) -> None:
    monkeypatch.delenv(MEMORY_RETRIEVAL_VARIABLE, raising=False)


def clear_memory_update_environment(monkeypatch) -> None:
    monkeypatch.delenv(MEMORY_UPDATE_VARIABLE, raising=False)


def clear_memory_prompt_environment(monkeypatch) -> None:
    for variable in MEMORY_PROMPT_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


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
    assert "MEMORY_RETRIEVAL_ENABLED=false" in contents
    assert "MEMORY_PROMPT_CONTEXT_ENABLED=false" in contents
    assert "MEMORY_UPDATE_ENABLED=false" in contents
    assert "MEMORY_PROMPT_MAX_RECORDS=5" in contents
    assert "MEMORY_PROMPT_MAX_CHARACTERS=2000" in contents


def test_memory_retrieval_is_disabled_by_default(monkeypatch) -> None:
    clear_memory_retrieval_environment(monkeypatch)

    configured = Settings(_env_file=None)

    assert configured.MEMORY_RETRIEVAL_ENABLED is False
    assert configured.REASONING_ENABLED is False
    assert configured.OLLAMA_MODEL == "llama3.2:3b"


@pytest.mark.parametrize(
    ("value", "expected"),
    (("true", True), ("false", False)),
)
def test_memory_retrieval_supports_boolean_override(
    monkeypatch, value: str, expected: bool
) -> None:
    clear_memory_retrieval_environment(monkeypatch)
    monkeypatch.setenv(MEMORY_RETRIEVAL_VARIABLE, value)

    assert (
        Settings(_env_file=None).MEMORY_RETRIEVAL_ENABLED is expected
    )


def test_invalid_memory_retrieval_boolean_is_rejected(monkeypatch) -> None:
    clear_memory_retrieval_environment(monkeypatch)
    monkeypatch.setenv(MEMORY_RETRIEVAL_VARIABLE, "sometimes")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_memory_prompt_defaults_are_safe_and_independent(monkeypatch) -> None:
    clear_memory_prompt_environment(monkeypatch)
    clear_memory_retrieval_environment(monkeypatch)
    clear_reasoning_environment(monkeypatch)
    clear_ollama_environment(monkeypatch)

    configured = Settings(_env_file=None)

    assert configured.MEMORY_PROMPT_CONTEXT_ENABLED is False
    assert configured.MEMORY_PROMPT_MAX_RECORDS == 5
    assert configured.MEMORY_PROMPT_MAX_CHARACTERS == 2000
    assert configured.MEMORY_RETRIEVAL_ENABLED is False
    assert configured.REASONING_ENABLED is False
    assert configured.OLLAMA_MODEL == "llama3.2:3b"


@pytest.mark.parametrize(
    ("variable", "value", "expected"),
    (
        ("MEMORY_PROMPT_CONTEXT_ENABLED", "true", True),
        ("MEMORY_PROMPT_CONTEXT_ENABLED", "false", False),
        ("MEMORY_PROMPT_MAX_RECORDS", "3", 3),
        ("MEMORY_PROMPT_MAX_CHARACTERS", "500", 500),
    ),
)
def test_memory_prompt_settings_support_overrides(
    monkeypatch, variable: str, value: str, expected: bool | int
) -> None:
    clear_memory_prompt_environment(monkeypatch)
    monkeypatch.setenv(variable, value)

    assert getattr(Settings(_env_file=None), variable) == expected


@pytest.mark.parametrize(
    ("variable", "value"),
    (
        ("MEMORY_PROMPT_CONTEXT_ENABLED", "sometimes"),
        ("MEMORY_PROMPT_MAX_RECORDS", "0"),
        ("MEMORY_PROMPT_MAX_RECORDS", "-1"),
        ("MEMORY_PROMPT_MAX_CHARACTERS", "0"),
        ("MEMORY_PROMPT_MAX_CHARACTERS", "-1"),
    ),
)
def test_invalid_memory_prompt_settings_are_rejected(
    monkeypatch, variable: str, value: str
) -> None:
    clear_memory_prompt_environment(monkeypatch)
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_memory_update_is_disabled_and_independent_by_default(
    monkeypatch,
) -> None:
    clear_memory_update_environment(monkeypatch)
    clear_memory_retrieval_environment(monkeypatch)
    clear_memory_prompt_environment(monkeypatch)
    clear_reasoning_environment(monkeypatch)
    clear_ollama_environment(monkeypatch)

    configured = Settings(_env_file=None)

    assert configured.MEMORY_UPDATE_ENABLED is False
    assert configured.MEMORY_RETRIEVAL_ENABLED is False
    assert configured.MEMORY_PROMPT_CONTEXT_ENABLED is False
    assert configured.REASONING_ENABLED is False
    assert configured.OLLAMA_MODEL == "llama3.2:3b"


@pytest.mark.parametrize(
    ("value", "expected"),
    (("true", True), ("false", False)),
)
def test_memory_update_supports_boolean_override(
    monkeypatch,
    value: str,
    expected: bool,
) -> None:
    clear_memory_update_environment(monkeypatch)
    monkeypatch.setenv(MEMORY_UPDATE_VARIABLE, value)

    assert Settings(_env_file=None).MEMORY_UPDATE_ENABLED is expected
