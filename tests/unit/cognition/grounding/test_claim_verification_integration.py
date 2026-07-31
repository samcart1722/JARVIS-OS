"""Sprint 19 integration at the structured claim provider boundary."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.grounding.claim_formatter import ClaimEvidenceFormatter
from app.cognition.grounding.claim_parser import JsonClaimEvidenceResponseParser
from app.cognition.grounding.claim_provider import ClaimEvidenceAttributionProvider
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.verification_models import (
    ClaimEvidenceVerificationEnvelope,
    ClaimEvidenceVerificationResult,
    ClaimSupportVerdict,
)
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)


def context(*records: str, snapshot: bool = True) -> CognitiveContext:
    if not snapshot:
        return CognitiveContext("request", "request")
    scope = MemoryScope("secret-scope")
    return CognitiveContext(
        "request",
        "request",
        memory_snapshot=MemorySnapshot(
            scope, tuple(ScopedMemoryRecord(scope, item) for item in records)
        ),
    )


def provider(inner: Mock, verifier: Mock | None) -> ClaimEvidenceAttributionProvider:
    return ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=3, max_characters=100),
        ClaimEvidenceFormatter(),
        verifier,
        enabled=True,
    )


def answered() -> ReasoningResult:
    return ReasoningResult(
        '{"status":"answered","claims":['
        '{"text":"first","used_record_numbers":[1]},'
        '{"text":"second","used_record_numbers":[2]}]}'
    )


def answered_three() -> ReasoningResult:
    return ReasoningResult(
        '{"status":"answered","claims":['
        '{"text":"first","used_record_numbers":[1]},'
        '{"text":"middle","used_record_numbers":[2]},'
        '{"text":"last","used_record_numbers":[3]}]}'
    )


def verification(*verdicts: str) -> ClaimEvidenceVerificationResult:
    return ClaimEvidenceVerificationResult(
        envelope=ClaimEvidenceVerificationEnvelope(
            "verified",
            tuple(
                ClaimSupportVerdict(index, verdict)
                for index, verdict in enumerate(verdicts, 1)
            ),
        )
    )


def test_disabled_verification_preserves_exact_sprint18_result_and_one_call() -> None:
    inner = Mock()
    inner.generate.return_value = answered()
    result = provider(inner, None).generate(context("one", "two"))
    assert result.response == (
        "Claim 1:\nfirst\nEvidence used: scoped memory records 1.\n\n"
        "Claim 2:\nsecond\nEvidence used: scoped memory records 2."
    )
    inner.generate.assert_called_once()


@pytest.mark.parametrize(
    ("current_context", "generated"),
    (
        (context(snapshot=False), ReasoningResult("pass-through")),
        (context(), ReasoningResult("pass-through")),
        (context("one"), ReasoningResult("", error_code="generator_failure")),
        (context("one"), ReasoningResult("invalid raw generation")),
        (
            context("one"),
            ReasoningResult('{"status":"insufficient_evidence","claims":[]}'),
        ),
    ),
)
def test_verifier_not_called_for_non_answered_paths(current_context, generated) -> None:
    inner = Mock()
    inner.generate.return_value = generated
    verifier = Mock()
    result = provider(inner, verifier).generate(current_context)
    verifier.verify.assert_not_called()
    inner.generate.assert_called_once()
    if generated.error_code or generated.response == "pass-through":
        assert result is generated


def test_all_supported_calls_verifier_once_and_formats_exactly_once() -> None:
    inner = Mock()
    inner.generate.return_value = answered()
    verifier = Mock()
    verifier.verify.return_value = verification("supported", "supported")
    formatter = Mock(wraps=ClaimEvidenceFormatter())
    instance = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=2, max_characters=100),
        formatter,
        verifier,
        enabled=True,
    )
    result = instance.generate(context("one", "two"))
    assert result.response.startswith("Claim 1:")
    inner.generate.assert_called_once()
    verifier.verify.assert_called_once()
    formatter.format.assert_called_once()
    envelope, selected = verifier.verify.call_args.args
    assert len(envelope.claims) == 2
    assert tuple(item.content for item in selected) == ("one", "two")


@pytest.mark.parametrize("unsupported_index", (0, 1, 2))
def test_any_unsupported_fails_closed_without_partial_claims(
    unsupported_index: int,
) -> None:
    verdicts = ["supported", "supported", "supported"]
    verdicts[unsupported_index] = "unsupported"
    inner = Mock()
    inner.generate.return_value = answered_three()
    verifier = Mock()
    verifier.verify.return_value = verification(*verdicts)
    formatter = Mock(wraps=ClaimEvidenceFormatter())
    instance = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=3, max_characters=100),
        formatter,
        verifier,
        enabled=True,
    )
    result = instance.generate(context("one", "two", "three"))
    assert (
        result.response
        == "Insufficient scoped memory evidence to answer the current request."
    )
    assert "first" not in result.response and "middle" not in result.response
    verifier.verify.assert_called_once()
    formatter.format.assert_not_called()


@pytest.mark.parametrize(
    ("supplied_code", "expected_code"),
    (
        (CAPABILITY_EXECUTION_FAILED, CAPABILITY_EXECUTION_FAILED),
        (
            CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
            CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
        ),
        ("unknown_verifier_failure", CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID),
    ),
)
def test_verifier_failure_only_preserves_known_cognitive_codes(
    supplied_code: str,
    expected_code: str,
) -> None:
    failure = ClaimEvidenceVerificationResult(error_code=supplied_code)
    inner = Mock()
    inner.generate.return_value = answered()
    verifier = Mock()
    verifier.verify.return_value = failure
    formatter = Mock(wraps=ClaimEvidenceFormatter())
    instance = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=2, max_characters=100),
        formatter,
        verifier,
        enabled=True,
    )
    result = instance.generate(context("one", "two"))
    assert result.response == "" and result.error_code == expected_code
    assert "first" not in result.response
    outcome = CognitiveOutcome(
        success=False,
        error=cognitive_error(result.error_code),
    )
    assert outcome.error is not None and outcome.error.code == expected_code
    inner.generate.assert_called_once()
    verifier.verify.assert_called_once()
    formatter.format.assert_not_called()


@pytest.mark.parametrize(
    "verdicts",
    (
        None,
        (ClaimSupportVerdict(1, "supported"),),
        (
            ClaimSupportVerdict(1, "supported"),
            ClaimSupportVerdict(2, "supported"),
            ClaimSupportVerdict(3, "supported"),
        ),
        (
            ClaimSupportVerdict(2, "supported"),
            ClaimSupportVerdict(3, "supported"),
        ),
    ),
)
def test_inconsistent_verifier_envelope_fails_closed_without_formatter(
    verdicts,
) -> None:
    inner = Mock()
    inner.generate.return_value = answered()
    verifier = Mock()
    verifier.verify.return_value = (
        SimpleNamespace(envelope=None, error_code=None)
        if verdicts is None
        else ClaimEvidenceVerificationResult(
            envelope=ClaimEvidenceVerificationEnvelope("verified", verdicts)
        )
    )
    formatter = Mock()
    instance = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=2, max_characters=100),
        formatter,
        verifier,
        enabled=True,
    )
    result = instance.generate(context("one", "two"))
    assert result == ReasoningResult(
        response="",
        error_code="claim_evidence_verification_protocol_invalid",
    )
    formatter.format.assert_not_called()
