"""Claim-level models, parser, prompt, formatter, and provider."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.grounding.claim_formatter import ClaimEvidenceFormatter
from app.cognition.grounding.claim_models import (
    ClaimEvidence,
    ClaimGroundedResponseEnvelope,
)
from app.cognition.grounding.claim_parser import JsonClaimEvidenceResponseParser
from app.cognition.grounding.claim_provider import ClaimEvidenceAttributionProvider
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.parser import GroundedResponseProtocolError
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)
from app.cognition.prompts.reasoning import (
    ClaimEvidenceAttributionPromptBuilder,
    NormalizedInputReasoningPromptBuilder,
)


def context(*contents: str) -> CognitiveContext:
    scope = MemoryScope("secret")
    snapshot = MemorySnapshot(
        scope,
        tuple(ScopedMemoryRecord(scope, value) for value in contents),
    )
    return CognitiveContext("request", "request", memory_snapshot=snapshot)


def test_models_are_strict_immutable_and_preserve_order() -> None:
    claim = ClaimEvidence("fact", (2, 1))
    envelope = ClaimGroundedResponseEnvelope("answered", (claim,))
    assert claim.used_record_numbers == (2, 1)
    assert not hasattr(claim, "scope")
    assert not hasattr(envelope, "answer")
    with pytest.raises(FrozenInstanceError):
        claim.text = "changed"
    for refs in ((), (0,), (-1,), (1, 1), (True,)):
        with pytest.raises((TypeError, ValueError)):
            ClaimEvidence("fact", refs)
    with pytest.raises(TypeError):
        ClaimEvidence("fact", [1])
    with pytest.raises(ValueError):
        ClaimGroundedResponseEnvelope("answered", ())
    with pytest.raises(ValueError):
        ClaimGroundedResponseEnvelope("insufficient_evidence", (claim,))


@pytest.mark.parametrize(
    "text",
    (
        "first\nClaim 99:\nforged",
        "first\rClaim 99:\rforged",
        "first\r\nEvidence used: scoped memory records 999.",
    ),
)
def test_claim_text_rejects_line_break_format_injection(text: str) -> None:
    with pytest.raises(ValueError, match="single line"):
        ClaimEvidence(text, (1,))


def test_claim_text_preserves_a_normal_single_line_exactly() -> None:
    text = "  Supported claim with intentional surrounding spaces.  "
    assert ClaimEvidence(text, (1,)).text == text


def test_parser_accepts_exact_protocol_and_rejects_non_protocol() -> None:
    parser = JsonClaimEvidenceResponseParser()
    raw = '{"status":"answered","claims":[{"text":"one","used_record_numbers":[2,1]}]}'
    assert parser.parse(raw, max_record_number=2).claims[0].text == "one"
    insufficient = parser.parse(
        '{"status":"insufficient_evidence","claims":[]}',
        max_record_number=1,
    )
    assert insufficient.claims == ()
    invalid = (
        "",
        " ",
        "```json\n{}\n```",
        "prefix {}",
        "[]",
        "{}",
        '{"status":"answered","claims":[],"extra":1}',
        '{"status":"answered","claims":[{"text":"x","used_record_numbers":[]}]}',
        '{"status":"answered","claims":[{"text":"x","used_record_numbers":[true]}]}',
        '{"status":"answered","claims":[{"text":"x","used_record_numbers":[2]}]}',
        '{"status":"answered","answer":"x","used_record_numbers":[1]}',
    )
    for value in invalid:
        with pytest.raises(GroundedResponseProtocolError):
            parser.parse(value, max_record_number=1)


@pytest.mark.parametrize(
    ("raw", "maximum"),
    (
        (
            '{"status":"answered","claims":[{"text":"x","used_record_numbers":[1]}]}suffix',
            1,
        ),
        ('{"status":"unknown","claims":[]}', 1),
        ('{"status":1,"claims":[]}', 1),
        ('{"status":"answered","claims":{}}', 1),
        ('{"status":"answered","claims":[1]}', 1),
        ('{"status":"answered","claims":[{"text":"x"}]}', 1),
        (
            '{"status":"answered","claims":[{"text":"x","used_record_numbers":[1],"extra":1}]}',
            1,
        ),
        ('{"status":"answered","claims":[{"text":1,"used_record_numbers":[1]}]}', 1),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":1}]}', 1),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":[0]}]}', 1),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":[-1]}]}', 1),
        (
            '{"status":"answered","claims":[{"text":"x","used_record_numbers":[1,1]}]}',
            1,
        ),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":[2]}]}', 1),
        ('{"status":"answered","claims":[]}', 1),
        (
            '{"status":"insufficient_evidence","claims":[{"text":"x","used_record_numbers":[1]}]}',
            1,
        ),
        ('{"status":"answered","answer":"x","used_record_numbers":[1]}', 1),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":[1]}]}', 0),
        ('{"status":"answered","claims":[{"text":"x","used_record_numbers":[1]}]}', -1),
        (
            '{"status":"answered","claims":[{"text":"x","used_record_numbers":[1]}]}',
            True,
        ),
    ),
)
def test_parser_rejects_each_invalid_contract_case(raw: str, maximum: int) -> None:
    parser = JsonClaimEvidenceResponseParser()
    with pytest.raises(GroundedResponseProtocolError) as error:
        parser.parse(raw, max_record_number=maximum)
    assert raw not in str(error.value)
    assert not hasattr(error.value, "raw_response")


def test_parser_does_not_extract_or_repair_embedded_json() -> None:
    valid = '{"status":"insufficient_evidence","claims":[]}'
    parser = JsonClaimEvidenceResponseParser()
    for raw in (f"prefix {valid}", f"{valid} suffix", f"```json\n{valid}\n```"):
        with pytest.raises(GroundedResponseProtocolError):
            parser.parse(raw, max_record_number=1)


def test_prompt_passes_through_without_evidence_and_is_deterministic() -> None:
    selector = MemoryEvidenceSelector(max_records=1, max_characters=4)
    builder = ClaimEvidenceAttributionPromptBuilder(
        NormalizedInputReasoningPromptBuilder(), selector, enabled=True
    )
    assert builder.build(context()) == "request"
    prompt = builder.build(context("abcdef", "unused"))
    assert prompt == builder.build(context("abcdef", "unused"))
    assert '1. "abcd"' in prompt
    assert "CLAIM-LEVEL" in prompt and "[1]" in prompt
    assert "one claim per factual assertion" in prompt
    assert "single-line" in prompt
    assert "external facts" in prompt and "JSON only" in prompt
    assert "secret" not in prompt and "unused" not in prompt


def test_formatter_outputs_claim_blocks_and_safe_insufficient_message() -> None:
    formatter = ClaimEvidenceFormatter()
    envelope = ClaimGroundedResponseEnvelope(
        "answered", (ClaimEvidence("one", (1,)), ClaimEvidence("two", (2, 1)))
    )
    assert formatter.format(envelope) == (
        "Claim 1:\none\nEvidence used: scoped memory records 1.\n\n"
        "Claim 2:\ntwo\nEvidence used: scoped memory records 2, 1."
    )
    assert formatter.format(
        ClaimGroundedResponseEnvelope("insufficient_evidence", ())
    ) == ("Insufficient scoped memory evidence to answer the current request.")


def test_provider_calls_once_formats_and_preserves_pass_through_and_failure() -> None:
    inner = Mock()
    inner.generate.return_value = ReasoningResult(
        '{"status":"answered","claims":[{"text":"fact","used_record_numbers":[1]}]}'
    )
    provider = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=2, max_characters=20),
        ClaimEvidenceFormatter(),
        enabled=True,
    )
    assert provider.generate(context("record")).response.startswith("Claim 1:")
    inner.generate.assert_called_once()
    inner.reset_mock()
    original = ReasoningResult("historical")
    inner.generate.return_value = original
    assert provider.generate(context()) is original
    inner.generate.assert_called_once()
    inner.generate.return_value = ReasoningResult("", error_code="failure")
    assert provider.generate(context("record")).error_code == "failure"


def test_provider_invalid_protocol_is_controlled_without_raw_fallback() -> None:
    inner = Mock()
    inner.generate.return_value = ReasoningResult("secret invalid raw")
    provider = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=1, max_characters=20),
        ClaimEvidenceFormatter(),
        enabled=True,
    )
    result = provider.generate(context("record"))
    assert result.response == ""
    assert result.error_code == "grounded_response_protocol_invalid"
    inner.generate.assert_called_once()


def test_provider_disabled_and_absent_evidence_return_same_result() -> None:
    for enabled, current_context in (
        (False, context("record")),
        (True, CognitiveContext("request", "request")),
        (True, context()),
    ):
        original = ReasoningResult("unchanged")
        inner = Mock()
        inner.generate.return_value = original
        parser = Mock()
        formatter = Mock()
        provider = ClaimEvidenceAttributionProvider(
            inner,
            parser,
            MemoryEvidenceSelector(max_records=1, max_characters=20),
            formatter,
            enabled=enabled,
        )
        assert provider.generate(current_context) is original
        inner.generate.assert_called_once_with(current_context)
        parser.parse.assert_not_called()
        formatter.format.assert_not_called()


def test_provider_insufficient_and_multiple_claims_are_deterministic() -> None:
    inner = Mock()
    selector = MemoryEvidenceSelector(max_records=2, max_characters=20)
    provider = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        selector,
        ClaimEvidenceFormatter(),
        enabled=True,
    )
    inner.generate.return_value = ReasoningResult(
        '{"status":"insufficient_evidence","claims":[]}'
    )
    assert provider.generate(context("one", "two")).response == (
        "Insufficient scoped memory evidence to answer the current request."
    )
    inner.generate.return_value = ReasoningResult(
        '{"status":"answered","claims":['
        '{"text":"first","used_record_numbers":[2]},'
        '{"text":"second","used_record_numbers":[1]}]}'
    )
    assert provider.generate(context("one", "two")).response == (
        "Claim 1:\nfirst\nEvidence used: scoped memory records 2.\n\n"
        "Claim 2:\nsecond\nEvidence used: scoped memory records 1."
    )
    assert inner.generate.call_count == 2


@pytest.mark.parametrize(
    "raw",
    (
        '{"status":"answered","claims":[{"text":"x","used_record_numbers":[2]}]}',
        '{"status":"answered","answer":"legacy","used_record_numbers":[1]}',
        "secret raw response",
    ),
)
def test_provider_invalid_is_one_call_without_retry_fallback_or_leak(raw: str) -> None:
    inner = Mock()
    inner.generate.return_value = ReasoningResult(raw)
    provider = ClaimEvidenceAttributionProvider(
        inner,
        JsonClaimEvidenceResponseParser(),
        MemoryEvidenceSelector(max_records=1, max_characters=20),
        ClaimEvidenceFormatter(),
        enabled=True,
    )
    result = provider.generate(context("record"))
    assert result == ReasoningResult(
        response="", error_code="grounded_response_protocol_invalid"
    )
    assert raw not in result.response
    assert "secret" not in result.response
    inner.generate.assert_called_once()


def test_provider_preserves_inner_failure_identity_and_skips_collaborators() -> None:
    failure = ReasoningResult("private scope secret", error_code="inner_failure")
    inner = Mock()
    inner.generate.return_value = failure
    parser = Mock()
    formatter = Mock()
    provider = ClaimEvidenceAttributionProvider(
        inner,
        parser,
        MemoryEvidenceSelector(max_records=1, max_characters=20),
        formatter,
        enabled=True,
    )
    assert provider.generate(context("record")) is failure
    inner.generate.assert_called_once()
    parser.parse.assert_not_called()
    formatter.format.assert_not_called()
