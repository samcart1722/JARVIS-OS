"""Proofs for the bounded deterministic list-command grammar."""

import pytest

from app.cognition.interpretation.interpreter import (
    DeterministicLocalCommandInterpreter,
)
from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
)
from app.cognition.interpretation.models import (
    LocalCommandInterpretationStatus as Status,
)
from app.cognition.interpretation.models import (
    LocalCommandInvalidReason as Reason,
)
from app.cognition.local_resolution.models import (
    AddListItemsCommand,
    ReadListItemsQuery,
)


@pytest.fixture
def interpreter():
    return DeterministicLocalCommandInterpreter()


def test_case_insensitive_read_maps_to_existing_query(interpreter) -> None:
    result = interpreter.interpret("LiSt ReAd groceries")
    assert result == LocalCommandInterpretation(
        Status.INTERPRETED, ReadListItemsQuery("groceries")
    )


def test_add_trims_preserves_and_orders_item_display_text(interpreter) -> None:
    result = interpreter.interpret("LIST add groceries ::  milk | Eggs | Gerber  ")
    assert result.intent == AddListItemsCommand(
        "groceries", ("milk", "Eggs", "Gerber")
    )


@pytest.mark.parametrize("text", ("", "  ", None, object()))
def test_empty_or_non_string_input_is_invalid(interpreter, text) -> None:
    result = interpreter.interpret(text)
    assert result.status is Status.INVALID
    assert result.invalid_reason is Reason.INVALID_INPUT


@pytest.mark.parametrize("text", ("list read", "list add :: milk"))
def test_missing_list_id_is_invalid(interpreter, text) -> None:
    assert interpreter.interpret(text).invalid_reason is Reason.MISSING_LIST_ID


def test_missing_add_separator_is_invalid(interpreter) -> None:
    result = interpreter.interpret("list add groceries milk")
    assert result.invalid_reason is Reason.MALFORMED_LIST_COMMAND


def test_missing_items_is_invalid(interpreter) -> None:
    result = interpreter.interpret("list add groceries :: ")
    assert result.invalid_reason is Reason.MISSING_ITEMS


@pytest.mark.parametrize(
    "text", ("list add groceries :: | eggs", "list add groceries :: milk |")
)
def test_empty_item_segment_is_invalid(interpreter, text) -> None:
    assert interpreter.interpret(text).invalid_reason is Reason.EMPTY_ITEM


@pytest.mark.parametrize(
    "text", ("list read groceries now", "list", "list remove groceries")
)
def test_malformed_list_namespace_is_invalid(interpreter, text) -> None:
    assert interpreter.interpret(text).status is Status.INVALID


def test_unrelated_text_is_not_interpreted(interpreter) -> None:
    result = interpreter.interpret("please remember milk")
    assert result == LocalCommandInterpretation(Status.NOT_INTERPRETED)


@pytest.mark.parametrize(
    "build",
    (
        lambda: LocalCommandInterpretation(Status.INTERPRETED),
        lambda: LocalCommandInterpretation(
            Status.INTERPRETED,
            ReadListItemsQuery("x"),
            Reason.MALFORMED_LIST_COMMAND,
        ),
        lambda: LocalCommandInterpretation(
            Status.NOT_INTERPRETED, ReadListItemsQuery("x")
        ),
        lambda: LocalCommandInterpretation(Status.INVALID),
    ),
)
def test_interpretation_invariants_reject_contradictions(build) -> None:
    with pytest.raises(ValueError):
        build()
