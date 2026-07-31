"""Independent verifier CLI tests without network."""

import os
from types import SimpleNamespace

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.core.config import Settings
from app.operations.independent_claim_verifier_demo_runtime import (
    INDEPENDENT_COMPARISON_COMPLETED,
    INDEPENDENT_COMPARISON_READINESS_FAILED,
    IndependentClaimVerifierDemoReport,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    readiness_result,
)
from scripts import demo_independent_claim_verifier as demo


@pytest.mark.parametrize(
    "argv",
    (
        (),
        ("--memory-scope", "s", "--memory-record", "r"),
        ("--memory-scope", " ", "--memory-record", "r", "p"),
    ),
)
def test_invalid_arguments_exit_two(argv) -> None:
    with pytest.raises(SystemExit) as error:
        demo.main(argv)
    assert error.value.code == 2


def test_success_uses_isolated_records_safe_output_and_environment(
    monkeypatch, capsys
) -> None:
    created = []

    def factory(settings, *, scoped_memory_records):
        item = SimpleNamespace(
            settings=settings,
            records=scoped_memory_records,
            provider_readiness_probe=object(),
            claim_verifier_readiness_probe=object(),
            cognitive_engine=object(),
        )
        created.append(item)
        return item

    monkeypatch.setattr(demo, "Container", factory)

    class Runtime:
        def __init__(self, **kwargs):
            assert kwargs["record_count"] == 2

        def run(self, prompt):
            assert prompt == "prompt"
            ready = readiness_result(READY)
            return IndependentClaimVerifierDemoReport(
                INDEPENDENT_COMPARISON_COMPLETED,
                ready,
                ready,
                CognitiveOutcome(success=True, response="shared"),
                CognitiveOutcome(success=True, response="independent"),
                2,
                True,
            )

    monkeypatch.setattr(demo, "IndependentClaimVerifierDemoRuntime", Runtime)
    before = os.environ.copy()
    code = demo.main(
        (
            "--memory-scope",
            "secret-scope",
            "--memory-record",
            "one",
            "--memory-record",
            "two",
            "--verifier-model",
            "verifier-secret-model",
            "prompt",
        )
    )
    output = capsys.readouterr().out
    assert code == 0 and len(created) == 2
    assert created[0].records == created[1].records
    shared_settings = created[0].settings
    independent_settings = created[1].settings
    assert shared_settings.MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED is False
    assert independent_settings.MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED is True
    assert shared_settings.OLLAMA_VERIFIER_MODEL is None
    assert independent_settings.OLLAMA_VERIFIER_MODEL == "verifier-secret-model"
    assert shared_settings.OLLAMA_MODEL == independent_settings.OLLAMA_MODEL
    assert shared_settings.OLLAMA_BASE_URL == independent_settings.OLLAMA_BASE_URL
    assert "SPRINT 19" in output and "SPRINT 20" in output
    for secret in (
        "secret-scope",
        "http://",
        "verifier-secret-model",
        "raw JSON",
        "Traceback",
    ):
        assert secret not in output
    assert os.environ == before


def test_settings_helper_does_not_mutate_base_and_preserves_primary_values() -> None:
    base = Settings(
        OLLAMA_BASE_URL="http://primary/generate",
        OLLAMA_MODEL="primary-model",
        _env_file=None,
    )
    before = base.model_dump()
    shared = demo._settings_for_demo(base, independent=False)
    independent = demo._settings_for_demo(
        base,
        independent=True,
        verifier_model="verifier-model",
    )
    assert base.model_dump() == before
    assert shared.OLLAMA_BASE_URL == independent.OLLAMA_BASE_URL
    assert shared.OLLAMA_MODEL == independent.OLLAMA_MODEL == "primary-model"
    assert shared.OLLAMA_VERIFIER_MODEL is None
    assert independent.OLLAMA_VERIFIER_MODEL == "verifier-model"


def test_unexpected_failure_is_safe_and_returns_one(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        demo,
        "Container",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("secret url")),
    )
    assert demo.main(("--memory-scope", "scope", "--memory-record", "r", "p")) == 1
    output = capsys.readouterr().out
    assert "failed safely" in output and "secret url" not in output


def test_readiness_failure_is_safe_and_returns_one(monkeypatch, capsys) -> None:
    created = SimpleNamespace(
        provider_readiness_probe=object(),
        claim_verifier_readiness_probe=object(),
        cognitive_engine=object(),
    )
    monkeypatch.setattr(demo, "Container", lambda *args, **kwargs: created)

    class Runtime:
        def __init__(self, **kwargs):
            pass

        def run(self, prompt):
            return IndependentClaimVerifierDemoReport(
                INDEPENDENT_COMPARISON_READINESS_FAILED,
                readiness_result(PROVIDER_UNAVAILABLE),
                readiness_result(READY),
                None,
                None,
                1,
                True,
            )

    monkeypatch.setattr(demo, "IndependentClaimVerifierDemoRuntime", Runtime)
    code = demo.main(("--memory-scope", "scope-secret", "--memory-record", "r", "p"))
    output = capsys.readouterr().out
    assert code == 1 and "No cognitive execution" in output
    assert "scope-secret" not in output and "Traceback" not in output


def test_inconsistent_report_presentation_fails_safely(monkeypatch, capsys) -> None:
    created = SimpleNamespace(
        provider_readiness_probe=object(),
        claim_verifier_readiness_probe=object(),
        cognitive_engine=object(),
    )
    monkeypatch.setattr(demo, "Container", lambda *args, **kwargs: created)

    class Runtime:
        def __init__(self, **kwargs):
            pass

        def run(self, prompt):
            ready = readiness_result(READY)
            return SimpleNamespace(
                status=INDEPENDENT_COMPARISON_COMPLETED,
                primary_readiness=ready,
                verifier_readiness=ready,
                shared_outcome=None,
                independent_outcome=None,
                record_count=1,
            )

    monkeypatch.setattr(demo, "IndependentClaimVerifierDemoRuntime", Runtime)
    assert (
        demo.main(("--memory-scope", "scope-secret", "--memory-record", "r", "p")) == 1
    )
    output = capsys.readouterr().out
    assert "failed safely" in output
    assert "scope-secret" not in output and "Traceback" not in output
