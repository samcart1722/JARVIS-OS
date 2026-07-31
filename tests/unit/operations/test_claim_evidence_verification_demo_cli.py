"""Sprint 19 CLI tests without external I/O."""

import os
from types import SimpleNamespace

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.core.config import Settings
from app.operations.claim_evidence_verification_demo_runtime import (
    VERIFICATION_COMPARISON_COMPLETED,
    ClaimEvidenceVerificationDemoReport,
)
from app.operations.provider_readiness import READY, readiness_result
from scripts import demo_claim_evidence_verification as demo


def success(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_settings_are_isolated_and_only_verification_differs() -> None:
    base = Settings(_env_file=None)
    sprint18 = demo._settings_for_demo(base, verification_enabled=False)
    sprint19 = demo._settings_for_demo(base, verification_enabled=True)
    assert sprint18.MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED is False
    assert sprint19.MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED is True
    assert sprint18.OLLAMA_MODEL == sprint19.OLLAMA_MODEL == base.OLLAMA_MODEL
    assert base.MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED is False


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


def test_success_is_safe_uses_two_isolated_containers_and_preserves_environment(
    monkeypatch, capsys
) -> None:
    created = []

    def factory(settings, *, scoped_memory_records):
        item = SimpleNamespace(
            settings=settings,
            records=scoped_memory_records,
            provider_readiness_probe=object(),
            cognitive_engine=object(),
        )
        created.append(item)
        return item

    monkeypatch.setattr(demo, "Container", factory)

    class Runtime:
        def __init__(self, **kwargs):
            assert kwargs["record_count"] == 2

        def run(self, prompt):
            return ClaimEvidenceVerificationDemoReport(
                VERIFICATION_COMPARISON_COMPLETED,
                "complete",
                readiness_result(READY),
                success("claim 18"),
                success("claim 19"),
                2,
                True,
            )

    monkeypatch.setattr(demo, "ClaimEvidenceVerificationDemoRuntime", Runtime)
    before = os.environ.copy()
    code = demo.main(
        (
            "--memory-scope",
            "real-secret",
            "--memory-record",
            "one",
            "--memory-record",
            "two",
            "prompt",
        )
    )
    output = capsys.readouterr().out
    assert code == 0 and len(created) == 2 and created[0].records == created[1].records
    assert "SPRINT 18" in output and "SPRINT 19" in output
    for secret in ("real-secret", "raw JSON", "http://", "Traceback"):
        assert secret not in output
    assert os.environ == before


def test_unexpected_failure_is_safe_and_returns_one(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        demo,
        "Container",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("raw secret http://private")
        ),
    )
    assert demo.main(("--memory-scope", "secret", "--memory-record", "r", "p")) == 1
    output = capsys.readouterr().out
    assert "failed safely" in output
    assert "raw secret" not in output and "Traceback" not in output
