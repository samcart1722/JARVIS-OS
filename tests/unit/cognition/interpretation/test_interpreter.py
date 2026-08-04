"""Proofs for the bounded deterministic list-command grammar."""

import json

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
    KnowledgeKind,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)


@pytest.fixture
def interpreter():
    return DeterministicLocalCommandInterpreter()


@pytest.fixture
def workspace():
    return WorkspaceIdentity("workspace")


def test_case_insensitive_read_maps_to_existing_query(interpreter, workspace) -> None:
    result = interpreter.interpret("LiSt ReAd groceries", workspace)
    assert result == LocalCommandInterpretation(
        Status.INTERPRETED, ReadListItemsQuery("groceries")
    )


def test_add_trims_preserves_and_orders_item_display_text(
    interpreter, workspace
) -> None:
    result = interpreter.interpret(
        "LIST add groceries ::  milk | Eggs | Gerber  ", workspace
    )
    assert result.intent == AddListItemsCommand(
        "groceries", ("milk", "Eggs", "Gerber")
    )


@pytest.mark.parametrize("text", ("", "  ", None, object()))
def test_empty_or_non_string_input_is_invalid(interpreter, workspace, text) -> None:
    result = interpreter.interpret(text, workspace)
    assert result.status is Status.INVALID
    assert result.invalid_reason is Reason.INVALID_INPUT


@pytest.mark.parametrize("text", ("list read", "list add :: milk"))
def test_missing_list_id_is_invalid(interpreter, workspace, text) -> None:
    assert (
        interpreter.interpret(text, workspace).invalid_reason
        is Reason.MISSING_LIST_ID
    )


def test_missing_add_separator_is_invalid(interpreter, workspace) -> None:
    result = interpreter.interpret("list add groceries milk", workspace)
    assert result.invalid_reason is Reason.MALFORMED_LIST_COMMAND


def test_missing_items_is_invalid(interpreter, workspace) -> None:
    result = interpreter.interpret("list add groceries :: ", workspace)
    assert result.invalid_reason is Reason.MISSING_ITEMS


@pytest.mark.parametrize(
    "text", ("list add groceries :: | eggs", "list add groceries :: milk |")
)
def test_empty_item_segment_is_invalid(interpreter, workspace, text) -> None:
    assert interpreter.interpret(text, workspace).invalid_reason is Reason.EMPTY_ITEM


@pytest.mark.parametrize(
    "text", ("list read groceries now", "list", "list remove groceries")
)
def test_malformed_list_namespace_is_invalid(interpreter, workspace, text) -> None:
    assert interpreter.interpret(text, workspace).status is Status.INVALID


def test_unrelated_text_is_not_interpreted(interpreter, workspace) -> None:
    result = interpreter.interpret("please remember milk", workspace)
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


def _store_payload(**overrides) -> str:
    fields = {
        "record_id": " family child diaper size ",
        "kind": "fact",
        "key": " child.diaper_size ",
        "value": " 4 ",
        "source_type": " user_asserted ",
        "source_reference": " actor:wife ",
    }
    fields.update(overrides)
    return json.dumps(fields)


@pytest.mark.parametrize("kind", tuple(KnowledgeKind))
def test_valid_store_maps_exact_fields_kind_and_workspace(
    interpreter, workspace, kind
) -> None:
    result = interpreter.interpret(
        f"KnOwLeDgE StOrE :: {_store_payload(kind=kind.value)}", workspace
    )
    assert result.status is Status.INTERPRETED
    assert isinstance(result.intent, StoreKnowledgeRecordCommand)
    record = result.intent.record
    assert record.workspace is workspace
    assert record.kind is kind
    assert (
        record.record_id,
        record.key,
        record.value,
        record.provenance.source_type,
        record.provenance.source_reference,
    ) == (
        "family child diaper size",
        "child.diaper_size",
        "4",
        "user_asserted",
        "actor:wife",
    )


def test_valid_read_maps_to_existing_query(interpreter, workspace) -> None:
    result = interpreter.interpret(
        'KNOWLEDGE READ :: {"record_id":" family child diaper size "}',
        workspace,
    )
    assert result.intent == ReadKnowledgeRecordQuery("family child diaper size")


@pytest.mark.parametrize("text", ("knowledgebase read :: {}", "knowledge.foo"))
def test_similar_text_outside_namespace_is_not_interpreted(
    interpreter, workspace, text
) -> None:
    assert interpreter.interpret(text, workspace).status is Status.NOT_INTERPRETED


@pytest.mark.parametrize(
    "text",
    (
        "knowledge",
        "knowledge remove :: {}",
        "knowledge read {}",
        "knowledge read:: {}",
    ),
)
def test_malformed_knowledge_prefix_is_terminal(interpreter, workspace, text) -> None:
    result = interpreter.interpret(text, workspace)
    assert result.invalid_reason is Reason.MALFORMED_KNOWLEDGE_COMMAND


def test_missing_knowledge_payload(interpreter, workspace) -> None:
    result = interpreter.interpret("knowledge read ::   ", workspace)
    assert result.invalid_reason is Reason.MISSING_KNOWLEDGE_PAYLOAD


@pytest.mark.parametrize(
    "payload",
    (
        "{",
        '{} trailing',
        "[]",
        '"value"',
        "null",
        "true",
        "1",
    ),
)
def test_invalid_knowledge_json(interpreter, workspace, payload) -> None:
    result = interpreter.interpret(f"knowledge read :: {payload}", workspace)
    assert result.invalid_reason is Reason.INVALID_KNOWLEDGE_JSON


@pytest.mark.parametrize(
    "command",
    (
        'knowledge read :: {"record_id":"one","record_id":"two"}',
        'knowledge read :: {"record_id":"one","extra":"x"}',
        "knowledge read :: {}",
        'knowledge read :: {"record_id":1}',
        'knowledge read :: {"record_id":" "}',
        'knowledge store :: {"record_id":"r"}',
        (
            'knowledge store :: {"record_id":"r","kind":"fact",'
            '"key":"k","value":"v","source_type":"s",'
            '"source_reference":"p","workspace":"forbidden"}'
        ),
        (
            'knowledge store :: {"record_id":"r","kind":"fact",'
            '"key":"k","value":"v","source_type":"s"}'
        ),
    ),
)
def test_invalid_knowledge_fields(interpreter, workspace, command) -> None:
    result = interpreter.interpret(command, workspace)
    assert result.invalid_reason is Reason.INVALID_KNOWLEDGE_FIELDS


def test_invalid_knowledge_kind(interpreter, workspace) -> None:
    result = interpreter.interpret(
        f"knowledge store :: {_store_payload(kind='opinion')}", workspace
    )
    assert result.invalid_reason is Reason.INVALID_KNOWLEDGE_KIND


def test_interpretation_invariants_accept_knowledge_and_reject_object(
    workspace,
) -> None:
    record = DeterministicLocalCommandInterpreter().interpret(
        f"knowledge store :: {_store_payload()}", workspace
    ).intent
    assert LocalCommandInterpretation(Status.INTERPRETED, record).intent is record
    with pytest.raises(ValueError):
        LocalCommandInterpretation(Status.INTERPRETED, object())


@pytest.mark.parametrize(
    ("payload", "reason"),
    (
        (
            '{"record_id":"r","kind":"fact","kind":"state","key":"k",'
            '"value":"v","source_type":"s","source_reference":"p"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        (
            '{"record_id":"r","kind":"fact","key":"k","value":{"x":"y"},'
            '"source_type":"s","source_reference":"p"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        (
            '{"record_id":"r","kind":"fact","key":"k","value":[],'
            '"source_type":"s","source_reference":"p"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        ('{"record_id":"r"} ::', Reason.INVALID_KNOWLEDGE_JSON),
        (
            '{"record_id":"r"}{"record_id":"s"}',
            Reason.INVALID_KNOWLEDGE_JSON,
        ),
        ('{"record_id":"r"} trailing', Reason.INVALID_KNOWLEDGE_JSON),
        ("{}", Reason.INVALID_KNOWLEDGE_FIELDS),
        (
            '{"record_id":"r","kind":"fact"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        (
            '{"record_id":"r","kind":"fact","key":"k","value":"v",'
            '"source_type":"s","source_reference":"p","workspace":"w"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        (
            '{"record_id":"r","kind":"FACT","key":"k","value":"v",'
            '"source_type":"s","source_reference":"p"}',
            Reason.INVALID_KNOWLEDGE_KIND,
        ),
        (
            '{"record_id":"r","kind":"fact","key":"k","value":1,'
            '"source_type":"s","source_reference":"p"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        (
            '{"record_id":"r","kind":"fact","key":"k","value":true,'
            '"source_type":"s","source_reference":"p"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
    ),
)
def test_difficult_knowledge_json_rejections(
    interpreter, workspace, payload, reason
) -> None:
    read_payloads = {
        '{"record_id":"r"} ::',
        '{"record_id":"r"}{"record_id":"s"}',
        '{"record_id":"r"} trailing',
        "{}",
        '{"record_id":"r","kind":"fact"}',
    }
    operation = "read" if payload in read_payloads else "store"
    result = interpreter.interpret(
        f"knowledge {operation} :: {payload}", workspace
    )
    assert result.status is Status.INVALID
    assert result.invalid_reason is reason


@pytest.mark.parametrize(
    ("expected", "ensure_ascii"),
    (('a"b', False), ("é", True)),
)
def test_json_escapes_are_decoded_and_preserved(
    interpreter, workspace, expected, ensure_ascii
) -> None:
    encoded_value = json.dumps(expected, ensure_ascii=ensure_ascii)
    payload = (
        '{"record_id":"r","kind":"fact","key":"k","value":'
        f'{encoded_value},"source_type":"s","source_reference":"p"}}'
    )
    result = interpreter.interpret(
        f"knowledge store :: {payload}", workspace
    )
    assert result.status is Status.INTERPRETED
    assert result.intent.record.value == expected


def test_knowledge_json_trailing_whitespace_is_accepted(
    interpreter, workspace
) -> None:
    result = interpreter.interpret(
        'knowledge read :: {"record_id":"r"} \t\r\n', workspace
    )
    assert result.status is Status.INTERPRETED
    assert result.intent == ReadKnowledgeRecordQuery("r")
