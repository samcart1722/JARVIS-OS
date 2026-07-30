"""Tests for functional demo CLI helpers without Ollama or network."""

import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord
from app.core.config import Settings
from app.core.container import Container
from app.operations.demo_runtime import (
    COMPARISON_SUCCEEDED,
    CognitiveDemoComparison,
    FunctionalCognitiveDemoRuntime,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    readiness_result,
)
from scripts import demo_reasoning
from scripts.demo_reasoning import (
    _demo_record_content,
    _settings_for_demo,
    main,
)


def test_demo_settings_enable_only_the_selected_comparison_path() -> None:
    base = Settings(
        REASONING_ENABLED=False,
        MEMORY_RETRIEVAL_ENABLED=False,
        MEMORY_PROMPT_CONTEXT_ENABLED=False,
        _env_file=None,
    )

    baseline = _settings_for_demo(base, memory_enabled=False)
    memory = _settings_for_demo(base, memory_enabled=True)

    assert baseline.REASONING_ENABLED is True
    assert baseline.MEMORY_RETRIEVAL_ENABLED is False
    assert baseline.MEMORY_PROMPT_CONTEXT_ENABLED is False
    assert memory.REASONING_ENABLED is True
    assert memory.MEMORY_RETRIEVAL_ENABLED is True
    assert memory.MEMORY_PROMPT_CONTEXT_ENABLED is True
    assert base.REASONING_ENABLED is False
    assert baseline.OLLAMA_BASE_URL == base.OLLAMA_BASE_URL
    assert memory.OLLAMA_BASE_URL == base.OLLAMA_BASE_URL
    assert baseline.OLLAMA_MODELS_URL == base.OLLAMA_MODELS_URL
    assert memory.OLLAMA_MODELS_URL == base.OLLAMA_MODELS_URL
    assert baseline.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert memory.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert baseline.OLLAMA_TIMEOUT_SECONDS == base.OLLAMA_TIMEOUT_SECONDS
    assert memory.OLLAMA_TIMEOUT_SECONDS == base.OLLAMA_TIMEOUT_SECONDS
    assert (
        baseline.MEMORY_PROMPT_MAX_RECORDS
        == base.MEMORY_PROMPT_MAX_RECORDS
    )
    assert (
        memory.MEMORY_PROMPT_MAX_CHARACTERS
        == base.MEMORY_PROMPT_MAX_CHARACTERS
    )


def test_demo_record_is_query_addressable_and_preserves_reference() -> None:
    content = _demo_record_content("What is Luxiom?", "Scoped reference")

    assert content == (
        "[DEMO RETRIEVAL KEY]\n"
        "What is Luxiom?\n\n"
        "[USER-PROVIDED REFERENCE]\n"
        "Scoped reference"
    )
    assert "Scoped reference" in content
    assert "demo-session" not in content


def test_demo_composition_isolates_memory_context_without_network() -> None:
    prompt = "What is Luxiom?"
    scope = MemoryScope("demo-session")
    record = ScopedMemoryRecord(
        scope=scope,
        content=_demo_record_content(prompt, "Scoped reference"),
    )
    other_scope = MemoryScope("other-session")
    excluded = ScopedMemoryRecord(
        scope=other_scope,
        content=_demo_record_content(prompt, "Excluded reference"),
    )
    base = Settings(_env_file=None)
    baseline = Container(_settings_for_demo(base, memory_enabled=False))
    memory = Container(
        _settings_for_demo(base, memory_enabled=True),
        scoped_memory_records=(record, excluded),
    )
    readiness_probe = Mock()
    readiness_probe.check.return_value = readiness_result(READY)
    baseline.ollama_client.chat = Mock(return_value="baseline response")
    memory.ollama_client.chat = Mock(return_value="memory response")

    result = FunctionalCognitiveDemoRuntime(
        readiness_probe=readiness_probe,
        baseline_engine=baseline.cognitive_engine,
        memory_engine=memory.cognitive_engine,
        memory_scope=scope,
        record_count=1,
    ).run(prompt)

    assert result.baseline_outcome is not None
    assert result.baseline_outcome.response == "baseline response"
    assert result.memory_outcome is not None
    assert result.memory_outcome.response == "memory response"
    readiness_probe.check.assert_called_once_with()
    baseline.ollama_client.chat.assert_called_once_with(prompt)
    memory_prompt = memory.ollama_client.chat.call_args.args[0]
    assert "[SCOPED MEMORY - UNTRUSTED REFERENCE DATA]" in memory_prompt
    assert "[USER-PROVIDED REFERENCE]\\nScoped reference" in memory_prompt
    assert "Excluded reference" not in memory_prompt
    assert scope.identifier not in memory_prompt
    assert other_scope.identifier not in memory_prompt
    assert baseline.ollama_client.model == memory.ollama_client.model
    assert baseline.ollama_client.url == memory.ollama_client.url


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
def test_cli_rejects_missing_or_blank_arguments_without_traceback(
    argv: tuple[str, ...],
    capsys,
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_cli_success_prints_safe_complete_report(
    monkeypatch,
    capsys,
) -> None:
    created: list[SimpleNamespace] = []
    environment_before = os.environ.copy()

    def fake_container(settings, *, scoped_memory_records=()):
        instance = SimpleNamespace(
            settings=settings,
            records=tuple(scoped_memory_records),
            provider_readiness_probe=object(),
            cognitive_engine=object(),
        )
        created.append(instance)
        return instance

    outcome = CognitiveOutcome(success=True, response="safe response")

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            assert kwargs["record_count"] == 2

        def run(self, prompt: str) -> CognitiveDemoComparison:
            assert prompt == "What is Luxiom?"
            return CognitiveDemoComparison(
                status=COMPARISON_SUCCEEDED,
                message="complete",
                readiness=readiness_result(READY),
                record_count=2,
                explicit_scope=True,
                baseline_outcome=outcome,
                memory_outcome=outcome,
            )

    monkeypatch.setattr(demo_reasoning, "Container", fake_container)
    monkeypatch.setattr(
        demo_reasoning,
        "FunctionalCognitiveDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "secret-scope-id",
            "--memory-record",
            "reference one",
            "--memory-record",
            "reference two",
            "What is Luxiom?",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Luxiom Functional Cognitive Demo v1" in output
    assert "Provider readiness: ready" in output
    assert "Explicit memory scope: yes" in output
    assert "Ephemeral scoped records: 2" in output
    assert "BASELINE — WITHOUT MEMORY CONTEXT" in output
    assert "MEMORY-AWARE — WITH SCOPED MEMORY CONTEXT" in output
    assert "Success: true" in output
    assert "secret-scope-id" not in output
    assert len(created) == 2
    assert created[0] is not created[1]
    assert created[0].records == ()
    assert len(created[1].records) == 2
    assert all(
        record.scope == MemoryScope("secret-scope-id")
        for record in created[1].records
    )
    assert "reference one" in created[1].records[0].content
    assert os.environ == environment_before


def test_cli_readiness_failure_prints_safe_non_execution(
    monkeypatch,
    capsys,
) -> None:
    fake_container = SimpleNamespace(
        provider_readiness_probe=object(),
        cognitive_engine=object(),
    )
    monkeypatch.setattr(
        demo_reasoning,
        "Container",
        lambda *args, **kwargs: fake_container,
    )

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, prompt: str) -> CognitiveDemoComparison:
            return CognitiveDemoComparison(
                status="readiness_failed",
                message="safe",
                readiness=readiness_result(PROVIDER_UNAVAILABLE),
                record_count=1,
                explicit_scope=True,
                baseline_outcome=None,
                memory_outcome=None,
            )

    monkeypatch.setattr(
        demo_reasoning,
        "FunctionalCognitiveDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-id",
            "--memory-record",
            "reference",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Provider readiness: provider_unavailable" in output
    assert "Cognitive execution performed: no" in output
    assert "hidden-id" not in output
    assert "Traceback" not in output


def test_cli_cognitive_failure_returns_one_and_prints_safe_error(
    monkeypatch,
    capsys,
) -> None:
    fake_container = SimpleNamespace(
        provider_readiness_probe=object(),
        cognitive_engine=object(),
    )
    monkeypatch.setattr(
        demo_reasoning,
        "Container",
        lambda *args, **kwargs: fake_container,
    )
    failure = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_EXECUTION_FAILED),
    )

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, prompt: str) -> CognitiveDemoComparison:
            return CognitiveDemoComparison(
                status=COMPARISON_SUCCEEDED,
                message="complete",
                readiness=readiness_result(READY),
                record_count=1,
                explicit_scope=True,
                baseline_outcome=failure,
                memory_outcome=failure,
            )

    monkeypatch.setattr(
        demo_reasoning,
        "FunctionalCognitiveDemoRuntime",
        FakeRuntime,
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-id",
            "--memory-record",
            "reference",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Success: false" in output
    assert f"Error code: {CAPABILITY_EXECUTION_FAILED}" in output
    assert "Traceback" not in output


def test_cli_unexpected_runtime_error_is_not_exposed(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        demo_reasoning,
        "Container",
        Mock(side_effect=RuntimeError("secret provider detail")),
    )

    exit_code = main(
        (
            "--memory-scope",
            "hidden-id",
            "--memory-record",
            "reference",
            "prompt",
        )
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Demo execution failed safely." in output
    assert "secret provider detail" not in output
    assert "hidden-id" not in output
    assert "Traceback" not in output
