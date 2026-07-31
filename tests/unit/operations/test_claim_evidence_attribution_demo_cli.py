"""Claim attribution CLI tests without network or filesystem."""

import os
from types import SimpleNamespace

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.core.config import Settings
from app.operations.claim_evidence_attribution_demo_runtime import (
    CLAIM_COMPARISON_COMPLETED,
    CLAIM_COMPARISON_READINESS_FAILED,
    ClaimEvidenceAttributionDemoReport,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    readiness_result,
)
from scripts import demo_claim_evidence_attribution as demo


def outcome(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_settings_are_isolated_and_preserve_provider_configuration() -> None:
    base = Settings(_env_file=None)
    sprint17 = demo._settings_for_claim_demo(base, claim_enabled=False)
    sprint18 = demo._settings_for_claim_demo(base, claim_enabled=True)
    assert sprint17 is not base and sprint18 is not base
    assert sprint17.MEMORY_GROUNDED_RESPONSE_ENABLED is True
    assert sprint17.MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED is False
    assert sprint18.MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED is True
    assert sprint17.OLLAMA_MODEL == sprint18.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert sprint17.OLLAMA_BASE_URL == sprint18.OLLAMA_BASE_URL
    assert base.MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED is False


@pytest.mark.parametrize(
    "argv",
    (
        (),
        ("--memory-scope", "scope", "--memory-record", "record"),
        ("--memory-record", "record", "prompt"),
        ("--memory-scope", "scope", "prompt"),
        ("--memory-scope", " ", "--memory-record", "record", "prompt"),
        ("--memory-scope", "scope", "--memory-record", " ", "prompt"),
        ("--memory-scope", "scope", "--memory-record", "record", " "),
    ),
)
def test_cli_required_and_blank_arguments_exit_two(argv, capsys) -> None:
    with pytest.raises(SystemExit) as error:
        demo.main(argv)
    assert error.value.code == 2
    assert "Traceback" not in capsys.readouterr().err


def patch_containers(monkeypatch) -> list[SimpleNamespace]:
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

    monkeypatch.setattr(demo, "Container", factory)
    return created


def test_success_multiple_records_is_safe_and_does_not_mutate_environment(
    monkeypatch, capsys
) -> None:
    created = patch_containers(monkeypatch)
    environment = os.environ.copy()

    class Runtime:
        def __init__(self, **kwargs):
            assert kwargs["record_count"] == 2

        def run(self, prompt):
            assert prompt == "same prompt"
            return ClaimEvidenceAttributionDemoReport(
                CLAIM_COMPARISON_COMPLETED,
                "complete",
                readiness_result(READY),
                outcome("Sprint 17"),
                outcome("Claim 1:\nclaim\nEvidence used: scoped memory records 1."),
                2,
                True,
            )

    monkeypatch.setattr(demo, "ClaimEvidenceAttributionDemoRuntime", Runtime)
    code = demo.main(
        (
            "--memory-scope",
            "real-secret-scope",
            "--memory-record",
            "one",
            "--memory-record",
            "two",
            "same prompt",
        )
    )
    output = capsys.readouterr().out
    assert code == 0
    assert len(created) == 2 and created[0].records == created[1].records
    assert "SPRINT 17" in output and "SPRINT 18" in output
    assert "real-secret-scope" not in output
    assert "raw JSON" not in output and "http://" not in output
    assert "Traceback" not in output
    assert os.environ == environment


def test_readiness_and_outcome_failures_return_one_safely(monkeypatch, capsys) -> None:
    patch_containers(monkeypatch)

    class Runtime:
        def __init__(self, **kwargs):
            pass

        def run(self, prompt):
            return ClaimEvidenceAttributionDemoReport(
                CLAIM_COMPARISON_READINESS_FAILED,
                "safe",
                readiness_result(PROVIDER_UNAVAILABLE),
                None,
                None,
                1,
                True,
            )

    monkeypatch.setattr(demo, "ClaimEvidenceAttributionDemoRuntime", Runtime)
    code = demo.main(("--memory-scope", "secret", "--memory-record", "one", "p"))
    assert code == 1
    assert "No cognitive execution" in capsys.readouterr().out


def test_unexpected_error_hides_scope_raw_url_and_stack(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        demo,
        "Container",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("secret raw JSON http://private")
        ),
    )
    code = demo.main(("--memory-scope", "scope-secret", "--memory-record", "r", "p"))
    output = capsys.readouterr().out
    assert code == 1
    assert "Demo execution failed safely." in output
    for secret in ("scope-secret", "raw JSON", "http://", "Traceback"):
        assert secret not in output
