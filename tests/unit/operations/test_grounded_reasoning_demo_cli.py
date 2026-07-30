"""Tests for the grounded reasoning CLI without network or filesystem."""

import os
from types import SimpleNamespace

import pytest

from app.cognition.domain.cognitive_outcome import (
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
    CognitiveOutcome,
    cognitive_error,
)
from app.core.config import Settings
from app.operations.grounded_reasoning_demo_runtime import (
    GROUNDED_COMPARISON_COMPLETED,
    GROUNDED_COMPARISON_READINESS_FAILED,
    GroundedReasoningDemoReport,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    readiness_result,
)
from scripts import demo_grounded_reasoning
from scripts.demo_grounded_reasoning import (
    _settings_for_grounded_demo,
    main,
)


def success(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_demo_settings_are_revalidated_isolated_and_preserve_provider() -> None:
    base = Settings(_env_file=None)

    standard = _settings_for_grounded_demo(
        base,
        grounded_enabled=False,
    )
    grounded = _settings_for_grounded_demo(
        base,
        grounded_enabled=True,
    )

    assert standard is not base
    assert grounded is not base
    assert standard.REASONING_ENABLED is True
    assert standard.MEMORY_RETRIEVAL_ENABLED is True
    assert standard.MEMORY_PROMPT_CONTEXT_ENABLED is True
    assert standard.MEMORY_GROUNDED_RESPONSE_ENABLED is False
    assert grounded.MEMORY_GROUNDED_RESPONSE_ENABLED is True
    assert grounded.OLLAMA_MODEL == standard.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert grounded.OLLAMA_BASE_URL == standard.OLLAMA_BASE_URL
    assert grounded.OLLAMA_TIMEOUT_SECONDS == standard.OLLAMA_TIMEOUT_SECONDS
    assert base.MEMORY_GROUNDED_RESPONSE_ENABLED is False


@pytest.mark.parametrize(
    "argv",
    (
        ("--memory-scope", "scope", "--memory-record", "record"),
        ("--memory-record", "record", "prompt"),
        ("--memory-scope", "scope", "prompt"),
        ("--memory-scope", " ", "--memory-record", "record", "prompt"),
        ("--memory-scope", "scope", "--memory-record", " ", "prompt"),
        ("--memory-scope", "scope", "--memory-record", "record", " "),
    ),
)
def test_cli_rejects_missing_or_blank_arguments(
    argv: tuple[str, ...],
    capsys,
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    assert "Traceback" not in capsys.readouterr().err


def _patch_containers(monkeypatch) -> list[SimpleNamespace]:
    created: list[SimpleNamespace] = []

    def factory(settings, *, scoped_memory_records):
        instance = SimpleNamespace(
            settings=settings,
            records=scoped_memory_records,
            provider_readiness_probe=object(),
            cognitive_engine=object(),
        )
        created.append(instance)
        return instance

    monkeypatch.setattr(demo_grounded_reasoning, "Container", factory)
    return created


def test_success_cli_prints_both_paths_without_scope(
    monkeypatch,
    capsys,
) -> None:
    created = _patch_containers(monkeypatch)
    environment_before = os.environ.copy()

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            assert kwargs["record_count"] == 2

        def run(self, prompt: str) -> GroundedReasoningDemoReport:
            return GroundedReasoningDemoReport(
                status=GROUNDED_COMPARISON_COMPLETED,
                message="complete",
                readiness=readiness_result(READY),
                standard_outcome=success("standard"),
                grounded_outcome=success(
                    "grounded\nEvidence used: scoped memory records 1, 2."
                ),
                record_count=2,
                explicit_scope=True,
            )

    monkeypatch.setattr(
        demo_grounded_reasoning,
        "GroundedReasoningDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--memory-record",
            "first",
            "--memory-record",
            "second",
            "Exact prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Provider readiness: ready" in output
    assert "STANDARD MEMORY-AWARE" in output
    assert "EVIDENCE-BOUNDED" in output
    assert "Evidence used: scoped memory records 1, 2." in output
    assert "hidden-scope" not in output
    assert len(created) == 2
    assert created[0].records == created[1].records
    assert os.environ == environment_before


def test_protocol_failure_is_printed_safely_and_returns_one(
    monkeypatch,
    capsys,
) -> None:
    _patch_containers(monkeypatch)
    failure = CognitiveOutcome(
        success=False,
        error=cognitive_error(GROUNDED_RESPONSE_PROTOCOL_INVALID),
    )

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, prompt: str) -> GroundedReasoningDemoReport:
            return GroundedReasoningDemoReport(
                status=GROUNDED_COMPARISON_COMPLETED,
                message="complete",
                readiness=readiness_result(READY),
                standard_outcome=success("standard"),
                grounded_outcome=failure,
                record_count=1,
                explicit_scope=True,
            )

    monkeypatch.setattr(
        demo_grounded_reasoning,
        "GroundedReasoningDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--memory-record",
            "record",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Code: grounded_response_protocol_invalid" in output
    assert "invalid evidence-bounded response" in output
    assert "hidden-scope" not in output
    assert "raw JSON" not in output


def test_readiness_failure_returns_one_without_engines(
    monkeypatch,
    capsys,
) -> None:
    _patch_containers(monkeypatch)

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, prompt: str) -> GroundedReasoningDemoReport:
            return GroundedReasoningDemoReport(
                status=GROUNDED_COMPARISON_READINESS_FAILED,
                message="safe",
                readiness=readiness_result(PROVIDER_UNAVAILABLE),
                standard_outcome=None,
                grounded_outcome=None,
                record_count=1,
                explicit_scope=True,
            )

    monkeypatch.setattr(
        demo_grounded_reasoning,
        "GroundedReasoningDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--memory-record",
            "record",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Provider readiness: provider_unavailable" in output
    assert "No cognitive execution was performed." in output
    assert "hidden-scope" not in output


def test_unexpected_error_is_safe_without_raw_details(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        demo_grounded_reasoning,
        "Container",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("secret raw provider response")
        ),
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-scope",
            "--memory-record",
            "record",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Demo execution failed safely." in output
    assert "secret raw provider response" not in output
    assert "hidden-scope" not in output
    assert "Traceback" not in output
