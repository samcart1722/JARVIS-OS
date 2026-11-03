"""Untrusted provider output must be one closed, bounded JSON object."""

import json

import pytest

from app.cognition.intent_preparation.models import Intent, ProviderOutcome
from app.cognition.intent_preparation.parser import CandidateParseError, parse_candidate


@pytest.mark.parametrize(
    ("intent", "semantic_fields"),
    [
        (Intent.CAPTURE_KNOWLEDGE, {"value": "café"}),
        (Intent.RECALL_KNOWLEDGE, {"key": "tema"}),
        (Intent.ADD_FOLLOW_UP, {"item": "pan", "list_id": "compras"}),
        (Intent.READ_FOLLOW_UP, {"list_id": "compras"}),
    ],
)
def test_parses_all_four_supported_intents(intent, semantic_fields) -> None:
    output = json.dumps(
        {"outcome": "supported", "intent": intent.value, "fields": semantic_fields}
    )
    candidate = parse_candidate(" \t\r\n" + output + "\r\n\t ")
    assert candidate.outcome is ProviderOutcome.SUPPORTED
    assert candidate.intent is intent
    assert dict(candidate.fields) == semantic_fields


@pytest.mark.parametrize("intent", list(Intent))
def test_empty_allowed_field_subset_is_a_partial_candidate(intent) -> None:
    candidate = parse_candidate(
        json.dumps({"outcome": "supported", "intent": intent.value, "fields": {}})
    )
    assert candidate.fields == ()


def test_partial_add_is_ordered_and_trims_only_frozen_edges() -> None:
    candidate = parse_candidate(
        json.dumps(
            {
                "outcome": "supported",
                "intent": "ADD_FOLLOW_UP",
                "fields": {"list_id": "\u3000Compras\u0085"},
            }
        )
    )
    assert candidate.fields == (("list_id", "Compras"),)


def test_exact_unsupported_result() -> None:
    candidate = parse_candidate('{"outcome":"unsupported","intent":null,"fields":{}}')
    assert candidate.outcome is ProviderOutcome.UNSUPPORTED
    assert candidate.intent is None
    assert candidate.fields == ()


@pytest.mark.parametrize(
    "provider_text",
    [
        None,
        b"{}",
        42,
        {},
        [],
        "",
        " ",
        "null",
        "[]",
        "true",
        '{"outcome":"supported","outcome":"supported","intent":"RECALL_KNOWLEDGE",'
        '"fields":{"key":"tema"}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE",'
        '"fields":{"key":"tema","key":"otro"}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE",'
        '"fields":{"key":{"nested":1,"nested":2}}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{},"fields":{}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{},"extra":0}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE"}',
        '{"outcome":"supported","fields":{}}',
        '{"intent":"RECALL_KNOWLEDGE","fields":{}}',
        '{"outcome":"supported","intent":"DELETE_KNOWLEDGE","fields":{}}',
        '{"outcome":"SUPPORTED","intent":"RECALL_KNOWLEDGE","fields":{}}',
        '{"outcome":true,"intent":"RECALL_KNOWLEDGE","fields":{}}',
        '{"outcome":"supported","intent":null,"fields":{}}',
        '{"outcome":"supported","intent":["RECALL_KNOWLEDGE"],"fields":{}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":[]}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"value":"x"}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"tool":"x"}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":null}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":12}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":true}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":[]}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":{}}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":""}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":"  "}}',
        '{"outcome":"supported","intent":"RECALL_KNOWLEDGE","fields":{"key":NaN}}',
        '{"outcome":"unsupported","intent":"RECALL_KNOWLEDGE","fields":{}}',
        '{"outcome":"unsupported","intent":null,"fields":{"key":"tema"}}',
        '{"command":"knowledge find :: tema"}',
        '{"tool":"list read","arguments":{"list_id":"compras"}}',
        "knowledge find :: tema",
        '```json\n{"outcome":"unsupported","intent":null,"fields":{}}\n```',
        'Result: {"outcome":"unsupported","intent":null,"fields":{}}',
        '{"outcome":"unsupported","intent":null,"fields":{}} listo',
        '{"outcome":"unsupported","intent":null,"fields":{}} {}',
        '{"outcome":"unsupported","intent":null,"fields":{}} null',
        '\u0085{"outcome":"unsupported","intent":null,"fields":{}}',
        '\ufeff{"outcome":"unsupported","intent":null,"fields":{}}',
    ],
)
def test_rejects_unclosed_ambiguous_or_executable_alternatives(provider_text) -> None:
    with pytest.raises(CandidateParseError):
        parse_candidate(provider_text)


def test_rejects_oversize_response_before_unbounded_parsing() -> None:
    for provider_text in (" " * 32769, "😀" * 8193):
        with pytest.raises(CandidateParseError):
            parse_candidate(provider_text)


def test_exact_response_byte_bound_includes_framing_whitespace() -> None:
    output = '{"outcome":"unsupported","intent":null,"fields":{}}'
    assert parse_candidate(output + " " * (32768 - len(output))).intent is None
    with pytest.raises(CandidateParseError):
        parse_candidate(output + " " * (32769 - len(output)))


@pytest.mark.parametrize("value", ["x" * 8193, "\ud800", "\udfff"])
def test_rejects_oversize_and_surrogate_semantic_fields(value) -> None:
    output = json.dumps(
        {
            "outcome": "supported",
            "intent": "CAPTURE_KNOWLEDGE",
            "fields": {"value": value},
        }
    )
    with pytest.raises(CandidateParseError):
        parse_candidate(output)


def test_rejects_raw_surrogate_and_deeply_nested_json_safely() -> None:
    for provider_text in ("\ud800", "[" * 2000 + "0" + "]" * 2000):
        with pytest.raises(CandidateParseError):
            parse_candidate(provider_text)
