"""Literal preservation and explicit list-destination role evidence."""

import pytest

from app.cognition.intent_preparation.grounding import check_grounding, check_roles
from app.cognition.intent_preparation.models import (
    EDGE_WHITESPACE,
    Candidate,
    Intent,
    ProviderOutcome,
)


def candidate(intent: Intent, **fields: str) -> Candidate:
    return Candidate(ProviderOutcome.SUPPORTED, intent, tuple(fields.items()))


def test_unicode_and_interior_whitespace_are_preserved() -> None:
    value = "Cafe\u0301\n  de Honduras ☕"
    data = candidate(Intent.CAPTURE_KNOWLEDGE, value=value)
    assert check_grounding(data, f"Conserva {value}") is None
    assert dict(data.fields)["value"] == value


@pytest.mark.parametrize(
    ("value", "original"),
    [
        ("MedSupply", "recuerda medsupply"),
        ("cafe", "recuerda café"),
        ("café", "recuerda cafe\u0301"),
        ("cafe\u0301", "recuerda café"),
        ("inventado", "recuerda verdadero"),
        ("dos espacios", "recuerda dos  espacios"),
        ("dos  espacios", "recuerda dos espacios"),
    ],
)
def test_grounding_rejects_rewriting(value: str, original: str) -> None:
    data = candidate(Intent.CAPTURE_KNOWLEDGE, value=value)
    assert check_grounding(data, original) == "non_grounded_field"


@pytest.mark.parametrize("edge", EDGE_WHITESPACE)
def test_only_frozen_outer_whitespace_is_trimmed(edge: str) -> None:
    data = candidate(Intent.RECALL_KNOWLEDGE, key=f"{edge}Café{edge}")
    assert data.fields == (("key", "Café"),)
    assert check_grounding(data, "Busca Café") is None


def test_zero_width_character_is_not_whitespace() -> None:
    data = candidate(Intent.CAPTURE_KNOWLEDGE, value="\u200bCafé")
    assert check_grounding(data, "Guarda Café") == "non_grounded_field"
    assert check_grounding(data, "Guarda \u200bCafé") is None


@pytest.mark.parametrize("text", [None, 42, "", " \u3000", "x" * 8193, "x\ud800"])
def test_invalid_original_input(text: object) -> None:
    assert check_grounding(candidate(Intent.RECALL_KNOWLEDGE, key="x"), text) == (
        "invalid_input"
    )


def test_surrogate_field_is_rejected_by_closed_model() -> None:
    with pytest.raises(ValueError):
        candidate(Intent.CAPTURE_KNOWLEDGE, value="valor\udfff")


@pytest.mark.parametrize(
    ("intent", "fields", "text"),
    [
        (Intent.CAPTURE_KNOWLEDGE, {"value": "contenido"}, "Conserva contenido"),
        (Intent.RECALL_KNOWLEDGE, {"key": "Café"}, "Busca Café"),
    ],
)
def test_capture_recall_closed_fields_and_grounding(
    intent: Intent, fields: dict[str, str], text: str
) -> None:
    data = candidate(intent, **fields)
    assert check_grounding(data, text) is None
    assert check_roles(data, text) is None


@pytest.mark.parametrize(
    ("intent", "field"),
    [
        (Intent.CAPTURE_KNOWLEDGE, "key"),
        (Intent.CAPTURE_KNOWLEDGE, "record_id"),
        (Intent.CAPTURE_KNOWLEDGE, "source_reference"),
        (Intent.RECALL_KNOWLEDGE, "kind"),
    ],
)
def test_capture_recall_cannot_acquire_metadata(intent: Intent, field: str) -> None:
    with pytest.raises(ValueError):
        candidate(intent, **{field: "literal"})


@pytest.mark.parametrize(
    "text",
    ["Pon llamar a la lista Inbox", "Pon llamar A LA LISTA Inbox"],
)
def test_add_explicit_terminal_destination(text: str) -> None:
    data = candidate(Intent.ADD_FOLLOW_UP, item="llamar", list_id="Inbox")
    assert check_grounding(data, text) is None
    assert check_roles(data, text) is None


@pytest.mark.parametrize(
    "text",
    [
        "Consulta la lista Pendientes",
        "¿Consulta la lista Pendientes?",
        "Consulta la lista Pendientes?",
        "¿Consulta la lista Pendientes",
        "LA LISTA Pendientes",
    ],
)
def test_read_destination_question_wrappers(text: str) -> None:
    data = candidate(Intent.READ_FOLLOW_UP, list_id="Pendientes")
    assert check_grounding(data, text) is None
    assert check_roles(data, text) is None


@pytest.mark.parametrize(
    "generic", ["mis pendientes", "mis tareas", "esa lista", "la lista"]
)
def test_generic_destination_never_defaults_list_id(generic: str) -> None:
    data = candidate(Intent.READ_FOLLOW_UP, list_id="Inbox")
    text = f"Consulta Inbox y {generic}"
    assert check_grounding(data, text) is None
    assert check_roles(data, text) == "missing_destination_evidence"


@pytest.mark.parametrize(
    ("intent", "text", "fields", "reason"),
    [
        (
            Intent.ADD_FOLLOW_UP,
            "Pon Inbox a mis pendientes",
            {"item": "Inbox", "list_id": "Inbox"},
            "missing_destination_evidence",
        ),
        (
            Intent.ADD_FOLLOW_UP,
            "Pon Inbox a la lista Otra",
            {"item": "Inbox", "list_id": "Inbox"},
            "wrong_role_field",
        ),
        (
            Intent.ADD_FOLLOW_UP,
            "Pon llamar a la lista Inbox",
            {"item": "Inbox", "list_id": "Inbox"},
            "wrong_role_field",
        ),
        (
            Intent.READ_FOLLOW_UP,
            "Menciona Inbox y consulta la lista Otra",
            {"list_id": "Inbox"},
            "wrong_role_field",
        ),
        (
            Intent.READ_FOLLOW_UP,
            "Consulta alala lista Inbox",
            {"list_id": "Inbox"},
            "missing_destination_evidence",
        ),
    ],
)
def test_wrong_role_occurrence(
    intent: Intent, text: str, fields: dict[str, str], reason: str
) -> None:
    data = candidate(intent, **fields)
    assert check_grounding(data, text) is None
    assert check_roles(data, text) == reason


@pytest.mark.parametrize(
    ("intent", "text"),
    [
        (Intent.ADD_FOLLOW_UP, 'Pon llamar " a la lista Inbox"'),
        (Intent.ADD_FOLLOW_UP, '"Pon llamar a la lista Inbox"'),
        (Intent.READ_FOLLOW_UP, 'Consulta "la lista Inbox"'),
        (Intent.READ_FOLLOW_UP, "Consulta “la lista Inbox”"),
    ],
)
def test_quoted_destination_is_not_evidence(intent: Intent, text: str) -> None:
    assert check_roles(candidate(intent, list_id="Inbox"), text) == (
        "missing_destination_evidence"
    )


@pytest.mark.parametrize(
    ("intent", "text"),
    [
        (Intent.ADD_FOLLOW_UP, "Pon llamar a la lista Primera a la lista Inbox"),
        (Intent.ADD_FOLLOW_UP, "Pon llamar a la lista Inbox a mis pendientes"),
        (Intent.ADD_FOLLOW_UP, 'Pon " a la lista Primera" llamar a la lista Inbox'),
        (Intent.READ_FOLLOW_UP, "Consulta la lista Primera y la lista Inbox"),
    ],
)
def test_multiple_destinations(intent: Intent, text: str) -> None:
    assert check_roles(candidate(intent, list_id="Inbox"), text) == (
        "ambiguous_destination"
    )


@pytest.mark.parametrize("list_id", ["dos tokens", "Inbox\nOtra", "A::B", "A\u00a0B"])
def test_list_id_constraints(list_id: str) -> None:
    data = candidate(Intent.READ_FOLLOW_UP, list_id=list_id)
    assert check_roles(data, f"Consulta la lista {list_id}") == "invalid_list_id"


def test_add_never_splits_items() -> None:
    data = candidate(Intent.ADD_FOLLOW_UP, item="uno|dos")
    assert check_roles(data, "Pon uno|dos a mis pendientes") == "invalid_item"


@pytest.mark.parametrize(
    ("intent", "fields", "text"),
    [
        (Intent.ADD_FOLLOW_UP, {}, "Pon llamar a mis pendientes"),
        (Intent.ADD_FOLLOW_UP, {"item": "llamar"}, "Pon llamar a mis pendientes"),
        (Intent.ADD_FOLLOW_UP, {"list_id": "Inbox"}, "Pon llamar a la lista Inbox"),
        (Intent.READ_FOLLOW_UP, {}, "Consulta mis pendientes"),
    ],
)
def test_partial_fields_remain_partial(
    intent: Intent, fields: dict[str, str], text: str
) -> None:
    assert check_roles(candidate(intent, **fields), text) is None


def test_partial_item_cannot_use_destination_only_occurrence() -> None:
    data = candidate(Intent.ADD_FOLLOW_UP, item="Inbox")
    assert check_roles(data, "Pon llamar a la lista Inbox") == "wrong_role_field"


@pytest.mark.parametrize(
    "intent,fields,source",
    [
        (Intent.CAPTURE_KNOWLEDGE, {"value": "Recuerda"}, "Recuerda que X"),
        (Intent.RECALL_KNOWLEDGE, {"key": "Qué"}, "Qué sabes de K"),
        (
            Intent.ADD_FOLLOW_UP,
            {"item": "Agrega", "list_id": "L"},
            "Agrega X a la lista L",
        ),
        (Intent.CAPTURE_KNOWLEDGE, {"value": "K"}, "Qué sabes de K"),
        (
            Intent.ADD_FOLLOW_UP,
            {"item": "llamar", "list_id": "L"},
            "Agrega llamar a MedSupply a la lista L",
        ),
    ],
)
def test_known_frozen_roles_cannot_use_keywords_or_partial_payloads(
    intent, fields, source
):
    data = Candidate(ProviderOutcome.SUPPORTED, intent, tuple(fields.items()))
    assert check_grounding(data, source) is None
    assert check_roles(data, source) == "wrong_role_field"


@pytest.mark.parametrize(
    "intent,fields,source",
    [
        (Intent.CAPTURE_KNOWLEDGE, {"value": "X"}, "Recuerda que X"),
        (Intent.RECALL_KNOWLEDGE, {"key": "K"}, "¿Qué sabes de K?"),
        (
            Intent.ADD_FOLLOW_UP,
            {"item": "llamar a MedSupply", "list_id": "L"},
            "Agrega llamar a MedSupply a la lista L",
        ),
        (Intent.READ_FOLLOW_UP, {"list_id": "L"}, "¿Qué hay en la lista L?"),
    ],
)
def test_known_frozen_role_slices_are_preserved(intent, fields, source):
    data = Candidate(ProviderOutcome.SUPPORTED, intent, tuple(fields.items()))
    assert check_grounding(data, source) is None
    assert check_roles(data, source) is None
