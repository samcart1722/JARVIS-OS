"""Model-assisted claim evidence support verification tests."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest
import requests

from app.cognition.grounding.claim_models import (
    ClaimEvidence,
    ClaimGroundedResponseEnvelope,
)
from app.cognition.grounding.evidence import SelectedMemoryEvidence
from app.cognition.grounding.verification_models import (
    ClaimEvidenceVerificationEnvelope,
    ClaimEvidenceVerificationResult,
    ClaimSupportVerdict,
)
from app.cognition.grounding.verification_parser import (
    ClaimEvidenceVerificationProtocolError,
    JsonClaimEvidenceVerificationParser,
)
from app.cognition.grounding.verification_prompt import (
    ClaimEvidenceVerificationPromptBuilder,
)
from app.cognition.grounding.verification_provider import OllamaClaimEvidenceVerifier


def generated() -> ClaimGroundedResponseEnvelope:
    return ClaimGroundedResponseEnvelope(
        "answered",
        (ClaimEvidence("first", (1,)), ClaimEvidence("second", (2, 1))),
    )


def evidence() -> tuple[SelectedMemoryEvidence, ...]:
    return (SelectedMemoryEvidence(1, "one"), SelectedMemoryEvidence(2, "two"))


def test_verification_models_are_strict_immutable_slots_and_safe() -> None:
    verdict = ClaimSupportVerdict(1, "supported")
    envelope = ClaimEvidenceVerificationEnvelope("verified", (verdict,))
    assert envelope.all_supported is True
    assert not hasattr(verdict, "scope") and not hasattr(envelope, "raw_response")
    with pytest.raises(FrozenInstanceError):
        verdict.verdict = "unsupported"
    for number in (True, 0, -1):
        with pytest.raises((TypeError, ValueError)):
            ClaimSupportVerdict(number, "supported")
    with pytest.raises(ValueError):
        ClaimSupportVerdict(1, "unknown")
    with pytest.raises(TypeError):
        ClaimSupportVerdict(1, 1)
    with pytest.raises(ValueError):
        ClaimEvidenceVerificationEnvelope("verified", ())
    with pytest.raises(ValueError):
        ClaimEvidenceVerificationEnvelope(
            "verified",
            (
                ClaimSupportVerdict(1, "supported"),
                ClaimSupportVerdict(1, "unsupported"),
            ),
        )
    with pytest.raises(ValueError):
        ClaimEvidenceVerificationResult()
    with pytest.raises(ValueError):
        ClaimEvidenceVerificationResult(envelope=envelope, error_code="failure")
    with pytest.raises(ValueError):
        ClaimEvidenceVerificationResult(error_code=" ")
    with pytest.raises(TypeError):
        ClaimEvidenceVerificationResult(envelope="invalid")


def test_parser_accepts_supported_unsupported_and_order_independent() -> None:
    parsed = JsonClaimEvidenceVerificationParser().parse(
        '{"status":"verified","claims":['
        '{"claim_number":2,"verdict":"unsupported"},'
        '{"claim_number":1,"verdict":"supported"}]}',
        claim_count=2,
    )
    assert parsed.claims[0].claim_number == 2
    assert parsed.all_supported is False


@pytest.mark.parametrize(
    ("raw", "count"),
    (
        ("", 1),
        (" ", 1),
        ("[]", 1),
        ("{}", 1),
        ("```json\n{}\n```", 1),
        ("prefix {}", 1),
        ("{} suffix", 1),
        ('{"status":"verified","status":"verified","claims":[]}', 1),
        ('{"status":"wrong","claims":[]}', 1),
        ('{"status":1,"claims":[]}', 1),
        ('{"status":"verified","claims":{}}', 1),
        ('{"status":"verified","claims":[],"extra":1}', 1),
        ('{"status":"verified","claims":[1]}', 1),
        ('{"status":"verified","claims":[{"claim_number":1}]}', 1),
        (
            '{"status":"verified","claims":[{"claim_number":1,"verdict":"supported","extra":1}]}',
            1,
        ),
        (
            '{"status":"verified","claims":[{"claim_number":true,"verdict":"supported"}]}',
            1,
        ),
        (
            '{"status":"verified","claims":[{"claim_number":0,"verdict":"supported"}]}',
            1,
        ),
        (
            '{"status":"verified","claims":[{"claim_number":-1,"verdict":"supported"}]}',
            1,
        ),
        ('{"status":"verified","claims":[{"claim_number":1,"verdict":1}]}', 1),
        ('{"status":"verified","claims":[{"claim_number":1,"verdict":"unknown"}]}', 1),
        (
            '{"status":"verified","claims":[{"claim_number":1,"verdict":"supported"},{"claim_number":1,"verdict":"supported"}]}',
            2,
        ),
        (
            '{"status":"verified","claims":[{"claim_number":1,"verdict":"supported"}]}',
            2,
        ),
        (
            '{"status":"verified","claims":[{"claim_number":2,"verdict":"supported"}]}',
            1,
        ),
        ('{"status":"answered","answer":"x","used_record_numbers":[1]}', 1),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":[1]}]}', 1),
        (
            '{"status":"verified","claims":[{"claim_number":1,"verdict":"supported"}]}',
            True,
        ),
    ),
)
def test_parser_rejects_invalid_protocol_without_raw_exposure(
    raw: str, count: int
) -> None:
    with pytest.raises(ClaimEvidenceVerificationProtocolError) as error:
        JsonClaimEvidenceVerificationParser().parse(raw, claim_count=count)
    if raw.strip():
        assert raw not in str(error.value)
    assert not hasattr(error.value, "raw_response")


def test_prompt_is_deterministic_scoped_to_citations_and_does_not_mutate() -> None:
    envelope = generated()
    selected = evidence() + (SelectedMemoryEvidence(3, "uncited secret"),)
    builder = ClaimEvidenceVerificationPromptBuilder()
    prompt = builder.build(envelope, selected)
    assert prompt == builder.build(envelope, selected)
    assert prompt.count('"claim_text":"first"') == 1
    assert prompt.count('"claim_text":"second"') == 1
    first_section = prompt.split('"claim_number":2')[0]
    assert '"record_number":2' not in first_section
    assert "uncited secret" not in prompt and "scope" not in prompt.lower()
    assert "untrusted" in prompt.lower() and "external knowledge" in prompt
    assert "JSON only" in prompt and "rationale" in prompt
    assert "exactly one verdict" in prompt
    assert "do not omit or add claim numbers" in prompt
    assert '"supported" and "unsupported"' in prompt
    assert envelope == generated() and selected[0].content == "one"


def test_ollama_verifier_calls_once_parses_once_and_fails_closed() -> None:
    client = Mock()
    parser = Mock()
    verified = ClaimEvidenceVerificationEnvelope(
        "verified",
        (ClaimSupportVerdict(1, "supported"), ClaimSupportVerdict(2, "supported")),
    )
    parser.parse.return_value = verified
    verifier = OllamaClaimEvidenceVerifier(
        client, ClaimEvidenceVerificationPromptBuilder(), parser
    )
    client.chat.return_value = "safe protocol"
    assert verifier.verify(generated(), evidence()) == ClaimEvidenceVerificationResult(
        envelope=verified
    )
    client.chat.assert_called_once()
    parser.parse.assert_called_once_with("safe protocol", claim_count=2)

    client.reset_mock()
    parser.reset_mock()
    client.chat.return_value = "secret malformed raw"
    parser.parse.side_effect = ClaimEvidenceVerificationProtocolError()
    result = verifier.verify(generated(), evidence())
    assert result.error_code == "claim_evidence_verification_protocol_invalid"
    assert "secret" not in str(result)
    client.chat.assert_called_once()
    parser.parse.assert_called_once()


@pytest.mark.parametrize(
    "operational_error",
    (requests.ConnectionError("private url"), requests.Timeout("private prompt")),
)
def test_ollama_verifier_operational_failure_is_controlled(
    operational_error,
) -> None:
    client = Mock()
    parser = Mock()
    verifier = OllamaClaimEvidenceVerifier(
        client, ClaimEvidenceVerificationPromptBuilder(), parser
    )
    client.chat.assert_not_called()
    client.chat.side_effect = operational_error
    result = verifier.verify(generated(), evidence())
    assert result == ClaimEvidenceVerificationResult(
        error_code="capability_execution_failed"
    )
    assert "private" not in str(result)
    client.chat.assert_called_once()
    parser.parse.assert_not_called()
