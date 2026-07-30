"""Tests for immutable grounded envelopes and strict JSON parsing."""

from dataclasses import FrozenInstanceError

import pytest

from app.cognition.grounding.models import (
    ANSWERED,
    INSUFFICIENT_EVIDENCE,
    GroundedResponseEnvelope,
)
from app.cognition.grounding.parser import (
    GroundedResponseProtocolError,
    JsonGroundedResponseParser,
)


def test_answered_envelope_is_immutable_and_has_no_scope() -> None:
    envelope = GroundedResponseEnvelope(
        status=ANSWERED,
        answer="Supported answer",
        used_record_numbers=(1, 2),
    )

    assert "scope" not in envelope.__dataclass_fields__
    with pytest.raises(FrozenInstanceError):
        envelope.answer = "changed"


@pytest.mark.parametrize(
    ("status", "answer", "references"),
    (
        (ANSWERED, "", (1,)),
        (ANSWERED, "answer", ()),
        (INSUFFICIENT_EVIDENCE, "ignored", (1,)),
        ("unknown", "answer", (1,)),
        (ANSWERED, "answer", (0,)),
        (ANSWERED, "answer", (-1,)),
        (ANSWERED, "answer", (1, 1)),
    ),
)
def test_envelope_rejects_invalid_invariants(
    status: str,
    answer: str,
    references: tuple[int, ...],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        GroundedResponseEnvelope(status, answer, references)


def test_parser_accepts_answered_and_insufficient_envelopes() -> None:
    parser = JsonGroundedResponseParser()

    answered = parser.parse(
        '{"status":"answered","answer":"Supported",'
        '"used_record_numbers":[1,2]}',
        max_record_number=2,
    )
    insufficient = parser.parse(
        '{"status":"insufficient_evidence","answer":"free text ignored",'
        '"used_record_numbers":[]}',
        max_record_number=2,
    )

    assert answered.used_record_numbers == (1, 2)
    assert insufficient.status == INSUFFICIENT_EVIDENCE
    assert insufficient.used_record_numbers == ()


@pytest.mark.parametrize(
    "raw",
    (
        "",
        " ",
        "```json\n{}\n```",
        'prefix {"status":"answered","answer":"a","used_record_numbers":[1]}',
        '{"status":"answered","answer":"a","used_record_numbers":[1]} suffix',
        "[]",
        '{"status":"answered","answer":"a"}',
        '{"status":"answered","answer":"a","used_record_numbers":[1],'
        '"extra":true}',
        '{"status":1,"answer":"a","used_record_numbers":[1]}',
        '{"status":"answered","answer":1,"used_record_numbers":[1]}',
        '{"status":"answered","answer":"a","used_record_numbers":"1"}',
        '{"status":"answered","answer":"a","used_record_numbers":[true]}',
        '{"status":"answered","answer":"a","used_record_numbers":[0]}',
        '{"status":"answered","answer":"a","used_record_numbers":[-1]}',
        '{"status":"answered","answer":"a","used_record_numbers":[1,1]}',
        '{"status":"answered","answer":"a","used_record_numbers":[]}',
        '{"status":"insufficient_evidence","answer":"x",'
        '"used_record_numbers":[1]}',
        '{"status":"unknown","answer":"a","used_record_numbers":[1]}',
    ),
)
def test_parser_rejects_malformed_protocol_without_raw_output(raw: str) -> None:
    parser = JsonGroundedResponseParser()

    with pytest.raises(GroundedResponseProtocolError) as error:
        parser.parse(raw, max_record_number=2)

    assert str(error.value) == (
        "The reasoning provider returned an invalid evidence-bounded response."
    )
    if len(raw.strip()) > 1:
        assert raw not in str(error.value)
    assert not hasattr(error.value, "raw_response")


def test_parser_rejects_out_of_range_and_is_deterministic() -> None:
    parser = JsonGroundedResponseParser()
    raw = (
        '{"status":"answered","answer":"Supported",'
        '"used_record_numbers":[2]}'
    )

    with pytest.raises(GroundedResponseProtocolError):
        parser.parse(raw, max_record_number=1)
    assert parser.parse(raw, max_record_number=2) == parser.parse(
        raw,
        max_record_number=2,
    )
