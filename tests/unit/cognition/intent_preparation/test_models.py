"""Closed, immutable semantic contracts carry no execution authority."""

from dataclasses import FrozenInstanceError, fields

import pytest

from app.cognition.intent_preparation.models import (
    EDGE_WHITESPACE,
    FIELD_ORDER,
    Candidate,
    EligibilityDecision,
    EligibilityResult,
    Intent,
    ProviderOutcome,
    ValidationResult,
    ValidationStatus,
    is_bounded_input,
    strip_edge_whitespace,
)


def test_closed_enum_values_and_domain_field_order() -> None:
    assert [intent.value for intent in Intent] == [
        "CAPTURE_KNOWLEDGE",
        "RECALL_KNOWLEDGE",
        "ADD_FOLLOW_UP",
        "READ_FOLLOW_UP",
    ]
    assert [outcome.value for outcome in ProviderOutcome] == [
        "supported",
        "unsupported",
    ]
    assert {decision.value for decision in EligibilityDecision} == {
        "eligible_unrecognized",
        "protected",
    }
    assert [state.value for state in ValidationStatus] == [
        "complete",
        "partial",
        "rejected",
    ]
    assert FIELD_ORDER[Intent.ADD_FOLLOW_UP] == ("item", "list_id")
    with pytest.raises(TypeError):
        FIELD_ORDER[Intent.ADD_FOLLOW_UP] = ("command",)


def test_candidate_is_frozen_and_canonicalizes_semantic_order_only() -> None:
    candidate = Candidate(
        ProviderOutcome.SUPPORTED,
        Intent.ADD_FOLLOW_UP,
        (("list_id", "\u3000Compras\u0085"), ("item", "  café  molido  ")),
    )
    assert candidate.fields == (("item", "café  molido"), ("list_id", "Compras"))
    with pytest.raises(FrozenInstanceError):
        candidate.intent = Intent.READ_FOLLOW_UP
    assert not hasattr(candidate, "__dict__")
    assert {field.name for field in fields(candidate)} == {
        "outcome",
        "intent",
        "fields",
    }


@pytest.mark.parametrize("intent", list(Intent))
def test_supported_partial_candidates_are_data_not_commands(intent: Intent) -> None:
    candidate = Candidate(ProviderOutcome.SUPPORTED, intent)
    assert candidate.fields == ()
    assert not hasattr(candidate, "command")


def test_unsupported_candidate_is_exactly_empty() -> None:
    assert Candidate(ProviderOutcome.UNSUPPORTED, None).fields == ()
    with pytest.raises((TypeError, ValueError)):
        Candidate(ProviderOutcome.UNSUPPORTED, Intent.CAPTURE_KNOWLEDGE)
    with pytest.raises((TypeError, ValueError)):
        Candidate(ProviderOutcome.UNSUPPORTED, None, (("value", "dato"),))


@pytest.mark.parametrize(
    "field_pairs",
    [
        (("value", "dato"), ("value", "otro")),
        (("key", "dato"),),
        (("record_id", "dato"),),
        (("command", "dato"),),
        (("value", "\u3000\u0085"),),
        (("value", None),),
        (("value", 1),),
        (("value", "x" * 8193),),
        (("value", "dato\ud800"),),
        {"value": "dato"},
        [("value", "dato")],
        (["value", "dato"],),
    ],
)
def test_candidate_rejects_invalid_or_authority_bearing_fields(field_pairs) -> None:
    with pytest.raises((TypeError, ValueError)):
        Candidate(ProviderOutcome.SUPPORTED, Intent.CAPTURE_KNOWLEDGE, field_pairs)


def test_candidate_never_coerces_enum_strings() -> None:
    with pytest.raises((TypeError, ValueError)):
        Candidate("supported", Intent.CAPTURE_KNOWLEDGE)
    with pytest.raises((TypeError, ValueError)):
        Candidate(ProviderOutcome.SUPPORTED, "CAPTURE_KNOWLEDGE")


def test_frozen_whitespace_is_explicit_and_preserves_nonmembers_and_interior() -> None:
    expected = {
        *range(0x0009, 0x000E),
        *range(0x001C, 0x0021),
        0x0085,
        0x00A0,
        0x1680,
        *range(0x2000, 0x200B),
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
    }
    assert {ord(character) for character in EDGE_WHITESPACE} == expected
    assert strip_edge_whitespace(EDGE_WHITESPACE + "café  café" + EDGE_WHITESPACE) == (
        "café  café"
    )
    assert strip_edge_whitespace("\u200bcafé\ufeff") == "\u200bcafé\ufeff"
    assert is_bounded_input("😀" * 8192)
    assert not is_bounded_input("😀" * 8193)


def test_result_models_are_frozen_closed_and_consistent() -> None:
    eligibility = EligibilityResult(EligibilityDecision.PROTECTED, "uncertain")
    with pytest.raises(FrozenInstanceError):
        eligibility.reason = "eligible"
    candidate = Candidate(ProviderOutcome.SUPPORTED, Intent.ADD_FOLLOW_UP)
    result = ValidationResult(ValidationStatus.PARTIAL, candidate, ("item", "list_id"))
    with pytest.raises(FrozenInstanceError):
        result.status = ValidationStatus.COMPLETE
    with pytest.raises((TypeError, ValueError)):
        ValidationResult(ValidationStatus.PARTIAL, candidate, ("list_id", "item"))
    with pytest.raises((TypeError, ValueError)):
        ValidationResult(ValidationStatus.COMPLETE, candidate)
    with pytest.raises((TypeError, ValueError)):
        ValidationResult(ValidationStatus.REJECTED, candidate, reason="invalid")
    with pytest.raises((TypeError, ValueError)):
        EligibilityResult("protected", "uncertain")
    for result_type in (EligibilityResult, ValidationResult):
        names = {field.name for field in fields(result_type)}
        assert names.isdisjoint(
            {
                "command",
                "actor",
                "workspace",
                "permission",
                "proof",
                "provider",
                "model",
            }
        )
