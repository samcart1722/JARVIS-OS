"""Validation accepts semantic data only after literal and role grounding."""

from dataclasses import fields

import pytest

from app.cognition.intent_preparation.eligibility import assess_eligibility
from app.cognition.intent_preparation.models import (
    Candidate,
    EligibilityDecision,
    Intent,
    ProviderOutcome,
    ValidationStatus,
)
from app.cognition.intent_preparation.validator import validate_candidate


def supported(intent: Intent, **semantic_fields: str) -> Candidate:
    return Candidate(ProviderOutcome.SUPPORTED, intent, tuple(semantic_fields.items()))


@pytest.mark.parametrize(
    ("candidate", "original"),
    [
        (
            supported(Intent.CAPTURE_KNOWLEDGE, value="café  molido"),
            "Conserva café  molido",
        ),
        (supported(Intent.RECALL_KNOWLEDGE, key="Tema Ágil"), "Busca Tema Ágil"),
        (
            supported(Intent.ADD_FOLLOW_UP, item="pan", list_id="Compras"),
            "Incorpora pan a la lista Compras",
        ),
        (
            supported(Intent.READ_FOLLOW_UP, list_id="Compras"),
            "Consulta la lista Compras",
        ),
        (
            supported(Intent.READ_FOLLOW_UP, list_id="Compras"),
            "¿Consulta la lista Compras?",
        ),
    ],
)
def test_complete_semantic_candidate_is_not_an_execution_result(candidate, original):
    result = validate_candidate(candidate, original)
    assert result.status is ValidationStatus.COMPLETE
    assert result.candidate == candidate
    assert result.missing_fields == ()
    assert result.reason is None
    assert {field.name for field in fields(result)} == {
        "status",
        "candidate",
        "missing_fields",
        "reason",
    }
    assert not hasattr(result, "command")


@pytest.mark.parametrize(
    ("intent", "semantic_fields", "original", "missing"),
    [
        (Intent.CAPTURE_KNOWLEDGE, {}, "Conserva dato", ("value",)),
        (Intent.RECALL_KNOWLEDGE, {}, "Busca tema", ("key",)),
        (
            Intent.ADD_FOLLOW_UP,
            {},
            "Incorpora pan a la lista compras",
            ("item", "list_id"),
        ),
        (Intent.ADD_FOLLOW_UP, {"item": "pan"}, "Incorpora pan", ("list_id",)),
        (
            Intent.ADD_FOLLOW_UP,
            {"list_id": "compras"},
            "Incorpora algo a la lista compras",
            ("item",),
        ),
        (Intent.READ_FOLLOW_UP, {}, "Consulta una lista", ("list_id",)),
    ],
)
def test_partial_semantics_report_missing_fields_in_frozen_order(
    intent, semantic_fields, original, missing
):
    result = validate_candidate(supported(intent, **semantic_fields), original)
    assert result.status is ValidationStatus.PARTIAL
    assert result.missing_fields == missing
    assert result.candidate is not None
    assert result.reason is None


@pytest.mark.parametrize(
    ("candidate", "original"),
    [
        (supported(Intent.CAPTURE_KNOWLEDGE, value="Café"), "Conserva café"),
        (supported(Intent.CAPTURE_KNOWLEDGE, value="cafe"), "Conserva café"),
        (supported(Intent.RECALL_KNOWLEDGE, key="café"), "Busca cafe\u0301"),
        (supported(Intent.RECALL_KNOWLEDGE, key="inventado"), "Busca tema"),
        (
            supported(Intent.ADD_FOLLOW_UP, item="pan", list_id="compras"),
            "La palabra compras aparece; incorpora pan a la lista hogar",
        ),
        (
            supported(Intent.READ_FOLLOW_UP, list_id="pendientes"),
            "Consulta mis pendientes",
        ),
        (supported(Intent.READ_FOLLOW_UP, list_id="tareas"), "Consulta mis tareas"),
        (supported(Intent.READ_FOLLOW_UP, list_id="lista"), "Consulta esa lista"),
        (supported(Intent.READ_FOLLOW_UP, list_id="lista"), "Consulta la lista"),
        (
            supported(Intent.ADD_FOLLOW_UP, item="pan", list_id="compras"),
            "Incorpora pan a la lista compras a la lista hogar",
        ),
        (
            supported(Intent.READ_FOLLOW_UP, list_id="compras"),
            "Consulta la lista hogar y la lista compras",
        ),
        (
            supported(Intent.READ_FOLLOW_UP, list_id="compras"),
            'La instrucción "consulta la lista compras" es un ejemplo',
        ),
        (
            supported(Intent.ADD_FOLLOW_UP, item="pan", list_id="dos listas"),
            "Incorpora pan a la lista dos listas",
        ),
        (
            supported(Intent.READ_FOLLOW_UP, list_id="compras::"),
            "Consulta la lista compras::",
        ),
        (
            supported(Intent.ADD_FOLLOW_UP, item="pan | leche", list_id="compras"),
            "Incorpora pan | leche a la lista compras",
        ),
    ],
)
def test_rejects_non_grounded_wrong_role_or_unserializable_semantics(
    candidate, original
):
    result = validate_candidate(candidate, original)
    assert result.status is ValidationStatus.REJECTED
    assert result.candidate is None
    assert result.missing_fields == ()
    assert result.reason
    assert original not in result.reason


@pytest.mark.parametrize("original", [None, [], "", "\u3000", "x" * 8193, "\ud800"])
def test_invalid_original_input_is_rejected(original) -> None:
    result = validate_candidate(
        supported(Intent.CAPTURE_KNOWLEDGE, value="dato"), original
    )
    assert result.status is ValidationStatus.REJECTED
    assert result.candidate is None


def test_untrusted_dict_and_closed_unsupported_do_not_gain_acceptance() -> None:
    for candidate in (
        {
            "outcome": "supported",
            "intent": "CAPTURE_KNOWLEDGE",
            "fields": {"value": "dato"},
        },
        Candidate(ProviderOutcome.UNSUPPORTED, None),
        None,
    ):
        result = validate_candidate(candidate, "Conserva dato")
        assert result.status is ValidationStatus.REJECTED
        assert result.candidate is None


def test_validator_rechecks_nominal_candidate_schema() -> None:
    candidate = supported(Intent.CAPTURE_KNOWLEDGE, value="dato")
    object.__setattr__(candidate, "fields", (("command", "dato"),))
    result = validate_candidate(candidate, "Conserva dato")
    assert result.status is ValidationStatus.REJECTED
    assert result.candidate is None


def test_validator_rejects_uninitialized_nominal_candidate_safely() -> None:
    candidate = object.__new__(Candidate)
    result = validate_candidate(candidate, "Conserva dato")
    assert result.status is ValidationStatus.REJECTED
    assert result.candidate is None


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("outcome", "supported"),
        ("intent", "CAPTURE_KNOWLEDGE"),
        ("fields", {"value": "dato"}),
        ("fields", (("value", "dato"), ("value", "otro"))),
        ("fields", (("value", "\ud800"),)),
        ("fields", (("value", "x" * 8193),)),
    ],
)
def test_validator_rejects_object_level_tampering(attribute, replacement) -> None:
    candidate = supported(Intent.CAPTURE_KNOWLEDGE, value="dato")
    object.__setattr__(candidate, attribute, replacement)
    result = validate_candidate(candidate, "Conserva dato")
    assert result.status is ValidationStatus.REJECTED
    assert result.candidate is None


def test_grounded_command_like_capture_payload_remains_inert_semantic_data() -> None:
    original = "Conserva literalmente knowledge find :: tema"
    candidate = supported(Intent.CAPTURE_KNOWLEDGE, value="knowledge find :: tema")
    result = validate_candidate(candidate, original)
    assert result.status is ValidationStatus.COMPLETE
    assert result.candidate == candidate
    assert not hasattr(result, "command")


@pytest.mark.parametrize(
    "original,intent,name,value",
    (
        ("Nunca conserves café", Intent.CAPTURE_KNOWLEDGE, "value", "café"),
        ("Recuerda que café", Intent.CAPTURE_KNOWLEDGE, "value", "café"),
        ("Nunca busques Tema Ágil", Intent.RECALL_KNOWLEDGE, "key", "Tema Ágil"),
        ("Qué sabes de Tema Ágil", Intent.RECALL_KNOWLEDGE, "key", "Tema Ágil"),
        ("No incorpora pan a la lista Compras", Intent.ADD_FOLLOW_UP, "item", "pan"),
        ("No consulta la lista Compras", Intent.READ_FOLLOW_UP, "list_id", "Compras"),
    ),
)
def test_complete_candidate_cannot_substitute_for_original_input_eligibility(
    original, intent, name, value
):
    fields_to_validate = {name: value}
    if intent is Intent.ADD_FOLLOW_UP:
        fields_to_validate["list_id"] = "Compras"
    before = assess_eligibility(original)
    result = validate_candidate(supported(intent, **fields_to_validate), original)
    assert result.status is ValidationStatus.COMPLETE
    assert before.decision is EligibilityDecision.PROTECTED
    assert assess_eligibility(original) == before
    assert not {"eligible", "authorized", "trusted", "executable", "command"} & {
        field.name for field in fields(result)
    }


@pytest.mark.parametrize(
    "intent,name,original,value",
    (
        (Intent.CAPTURE_KNOWLEDGE, "value", "Conserva café", "café"),
        (Intent.RECALL_KNOWLEDGE, "key", "Busca Tema Ágil", "Tema Ágil"),
    ),
)
def test_eligibility_does_not_replace_grounding_of_the_exact_original_input(
    intent, name, original, value
):
    candidate = supported(intent, **{name: value})
    assert assess_eligibility(original).decision is (
        EligibilityDecision.ELIGIBLE_UNRECOGNIZED
    )
    assert validate_candidate(candidate, original).status is ValidationStatus.COMPLETE
    other_original = "Hola"
    assert assess_eligibility(other_original).decision is (
        EligibilityDecision.ELIGIBLE_UNRECOGNIZED
    )
    result = validate_candidate(candidate, other_original)
    assert result.status is ValidationStatus.REJECTED
    assert result.reason == "non_grounded_field"


def test_eligible_unknown_intent_may_receive_closed_unsupported_without_authority():
    original = "Hola"
    assert assess_eligibility(original).reason == "safe_unrecognized"
    result = validate_candidate(Candidate(ProviderOutcome.UNSUPPORTED, None), original)
    assert result.status is ValidationStatus.REJECTED
    assert result.reason == "unsupported"
    assert result.candidate is None
