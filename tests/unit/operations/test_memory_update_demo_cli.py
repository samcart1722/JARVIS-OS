"""Tests for the explicit memory update CLI without network or filesystem."""

import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.core.config import Settings
from app.operations.memory_update_demo_runtime import (
    MEMORY_UPDATE_COMPLETED,
    MEMORY_UPDATE_READINESS_FAILED,
    ExplicitMemoryUpdateDemoReport,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    readiness_result,
)
from scripts import demo_memory_update
from scripts.demo_memory_update import _settings_for_update_demo, main


def success(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_update_demo_settings_are_revalidated_and_isolated() -> None:
    base = Settings(
        REASONING_ENABLED=False,
        MEMORY_RETRIEVAL_ENABLED=False,
        MEMORY_PROMPT_CONTEXT_ENABLED=False,
        MEMORY_UPDATE_ENABLED=False,
        _env_file=None,
    )

    configured = _settings_for_update_demo(base)

    assert configured is not base
    assert configured.REASONING_ENABLED is True
    assert configured.MEMORY_RETRIEVAL_ENABLED is True
    assert configured.MEMORY_PROMPT_CONTEXT_ENABLED is True
    assert configured.MEMORY_UPDATE_ENABLED is True
    assert configured.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert configured.OLLAMA_BASE_URL == base.OLLAMA_BASE_URL
    assert configured.OLLAMA_MODELS_URL == base.OLLAMA_MODELS_URL
    assert configured.OLLAMA_TIMEOUT_SECONDS == base.OLLAMA_TIMEOUT_SECONDS
    assert (
        configured.MEMORY_PROMPT_MAX_RECORDS
        == base.MEMORY_PROMPT_MAX_RECORDS
    )
    assert base.MEMORY_UPDATE_ENABLED is False


@pytest.mark.parametrize(
    "argv",
    (
        ("--memory-scope", "scope", "--remember", "record"),
        ("--remember", "record", "prompt"),
        ("--memory-scope", "scope", "prompt"),
        ("--memory-scope", " ", "--remember", "record", "prompt"),
        ("--memory-scope", "scope", "--remember", " ", "prompt"),
        ("--memory-scope", "scope", "--remember", "record", " "),
    ),
)
def test_cli_rejects_missing_or_blank_arguments(
    argv: tuple[str, ...],
    capsys,
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def _patch_container(monkeypatch) -> list[SimpleNamespace]:
    created: list[SimpleNamespace] = []

    def factory(settings):
        instance = SimpleNamespace(
            settings=settings,
            provider_readiness_probe=object(),
            cognitive_engine=object(),
            explicit_memory_update_service=object(),
        )
        created.append(instance)
        return instance

    monkeypatch.setattr(demo_memory_update, "Container", factory)
    return created


def test_successful_cli_prints_complete_safe_report(
    monkeypatch,
    capsys,
) -> None:
    created = _patch_container(monkeypatch)
    environment_before = os.environ.copy()
    outcome = success("safe response")

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            assert len(kwargs["contents"]) == 2
            assert "first payload" in kwargs["contents"][0]
            assert "second payload" in kwargs["contents"][1]
            assert "hidden-scope" not in "".join(kwargs["contents"])

        def run(self, prompt: str) -> ExplicitMemoryUpdateDemoReport:
            assert prompt == "Exact prompt"
            return ExplicitMemoryUpdateDemoReport(
                status=MEMORY_UPDATE_COMPLETED,
                message="complete",
                readiness=readiness_result(READY),
                before_outcome=outcome,
                after_outcome=outcome,
                records_requested=2,
                records_written=2,
                explicit_scope=True,
            )

    monkeypatch.setattr(
        demo_memory_update,
        "ExplicitMemoryUpdateDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--remember",
            "first payload",
            "--remember",
            "second payload",
            "Exact prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Provider readiness: ready" in output
    assert "Explicit memory scope: yes" in output
    assert "Records requested: 2" in output
    assert "Records written: 2" in output
    assert "Persistence: none" in output
    assert "BEFORE EXPLICIT MEMORY UPDATE" in output
    assert "AFTER EXPLICIT MEMORY UPDATE" in output
    assert "hidden-scope" not in output
    assert len(created) == 1
    assert created[0].settings.MEMORY_UPDATE_ENABLED is True
    assert os.environ == environment_before


def test_readiness_failure_returns_one_without_outcomes(
    monkeypatch,
    capsys,
) -> None:
    _patch_container(monkeypatch)

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, prompt: str) -> ExplicitMemoryUpdateDemoReport:
            return ExplicitMemoryUpdateDemoReport(
                status=MEMORY_UPDATE_READINESS_FAILED,
                message="safe",
                readiness=readiness_result(PROVIDER_UNAVAILABLE),
                before_outcome=None,
                after_outcome=None,
                records_requested=1,
                records_written=0,
                explicit_scope=True,
            )

    monkeypatch.setattr(
        demo_memory_update,
        "ExplicitMemoryUpdateDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--remember",
            "payload",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Provider readiness: provider_unavailable" in output
    assert "Records written: 0" in output
    assert "No cognitive execution or memory update was performed." in output
    assert "hidden-scope" not in output


def test_cognitive_failure_returns_one_with_safe_error(
    monkeypatch,
    capsys,
) -> None:
    _patch_container(monkeypatch)
    failure = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_EXECUTION_FAILED),
    )

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, prompt: str) -> ExplicitMemoryUpdateDemoReport:
            return ExplicitMemoryUpdateDemoReport(
                status=MEMORY_UPDATE_COMPLETED,
                message="complete",
                readiness=readiness_result(READY),
                before_outcome=failure,
                after_outcome=failure,
                records_requested=1,
                records_written=1,
                explicit_scope=True,
            )

    monkeypatch.setattr(
        demo_memory_update,
        "ExplicitMemoryUpdateDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--remember",
            "payload",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Success: false" in output
    assert f"Error code: {CAPABILITY_EXECUTION_FAILED}" in output
    assert "Traceback" not in output


def test_operational_or_write_failure_is_not_exposed(
    monkeypatch,
    capsys,
) -> None:
    _patch_container(monkeypatch)
    monkeypatch.setattr(
        demo_memory_update,
        "ExplicitMemoryUpdateDemoRuntime",
        Mock(side_effect=RuntimeError("secret write detail")),
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--remember",
            "payload",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Records written: not confirmed" in output
    assert "secret write detail" not in output
    assert "hidden-scope" not in output
    assert "Traceback" not in output
