"""Proofs for the bounded deterministic list-command grammar."""

import json
from dataclasses import FrozenInstanceError, fields
from inspect import signature

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
    BrowseAfterKnowledgeRecordsQuery,
    BrowseKnowledgeRecordsQuery,
    FindKnowledgeRecordsQuery,
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
    assert result.intent == AddListItemsCommand("groceries", ("milk", "Eggs", "Gerber"))


@pytest.mark.parametrize("text", ("", "  ", None, object()))
def test_empty_or_non_string_input_is_invalid(interpreter, workspace, text) -> None:
    result = interpreter.interpret(text, workspace)
    assert result.status is Status.INVALID
    assert result.invalid_reason is Reason.INVALID_INPUT


@pytest.mark.parametrize("text", ("list read", "list add :: milk"))
def test_missing_list_id_is_invalid(interpreter, workspace, text) -> None:
    assert (
        interpreter.interpret(text, workspace).invalid_reason is Reason.MISSING_LIST_ID
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


@pytest.mark.parametrize("kind", (None, *tuple(KnowledgeKind)))
def test_valid_find_maps_exact_key_and_optional_kind(
    interpreter, workspace, kind
) -> None:
    kind_field = "" if kind is None else f',"kind":"{kind.value}"'
    result = interpreter.interpret(
        f'KnOwLeDgE FiNd :: {{"key":" child.diaper_size "{kind_field}}}',
        workspace,
    )
    assert result.intent == FindKnowledgeRecordsQuery("child.diaper_size", kind)


def test_find_accepts_reversed_fields(interpreter, workspace) -> None:
    result = interpreter.interpret(
        'knowledge find :: {"kind":"fact","key":"child.diaper_size"}', workspace
    )
    assert result.intent == FindKnowledgeRecordsQuery(
        "child.diaper_size", KnowledgeKind.FACT
    )


@pytest.mark.parametrize(
    ("text", "reason"),
    (
        ("knowledge find", Reason.MALFORMED_KNOWLEDGE_COMMAND),
        ("knowledge find {}", Reason.MALFORMED_KNOWLEDGE_COMMAND),
        ("knowledge find :: ", Reason.MISSING_KNOWLEDGE_PAYLOAD),
        ("knowledge find :: {", Reason.INVALID_KNOWLEDGE_JSON),
        ('knowledge find :: {"key":"k"} trailing', Reason.INVALID_KNOWLEDGE_JSON),
        ('knowledge find :: {"key":"a","key":"b"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        (
            'knowledge find :: {"key":"k","kind":"fact","kind":"state"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        ('knowledge find :: {"Key":"k"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        (
            'knowledge find :: {"key":"k","workspace":"w"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        ('knowledge find :: {"key":"k","extra":"x"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ("knowledge find :: {}", Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge find :: {"key":" "}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge find :: {"key":1}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge find :: {"key":"k","kind":1}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge find :: {"key":"k","kind":"FACT"}', Reason.INVALID_KNOWLEDGE_KIND),
        (
            'knowledge find :: {"key":"k","kind":"opinion"}',
            Reason.INVALID_KNOWLEDGE_KIND,
        ),
        ("knowledge find :: []", Reason.INVALID_KNOWLEDGE_JSON),
        ('knowledge find :: "k"', Reason.INVALID_KNOWLEDGE_JSON),
        ("knowledge find :: null", Reason.INVALID_KNOWLEDGE_JSON),
        ("knowledge find :: true", Reason.INVALID_KNOWLEDGE_JSON),
        ("knowledge find :: 1", Reason.INVALID_KNOWLEDGE_JSON),
    ),
)
def test_invalid_find_has_exact_terminal_reason(
    interpreter, workspace, text, reason
) -> None:
    result = interpreter.interpret(text, workspace)
    assert result.status is Status.INVALID
    assert result.invalid_reason is reason


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
        "{} trailing",
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
    record = (
        DeterministicLocalCommandInterpreter()
        .interpret(f"knowledge store :: {_store_payload()}", workspace)
        .intent
    )
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
    result = interpreter.interpret(f"knowledge {operation} :: {payload}", workspace)
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
    result = interpreter.interpret(f"knowledge store :: {payload}", workspace)
    assert result.status is Status.INTERPRETED
    assert result.intent.record.value == expected


def test_knowledge_json_trailing_whitespace_is_accepted(interpreter, workspace) -> None:
    result = interpreter.interpret(
        'knowledge read :: {"record_id":"r"} \t\r\n', workspace
    )
    assert result.status is Status.INTERPRETED
    assert result.intent == ReadKnowledgeRecordQuery("r")


@pytest.mark.parametrize(
    "text",
    (
        "knowledge browse :: {}",
        " KnOwLeDgE BrOwSe ::{} \t\n",
        "knowledge\tbrowse\n:: {\n\t}",
    ),
)
def test_browse_interpretation_accepts_only_empty_object(interpreter, workspace, text):
    result = interpreter.interpret(text, workspace)
    assert result.status is Status.INTERPRETED
    assert type(result.intent) is BrowseKnowledgeRecordsQuery
    assert result.invalid_reason is None


@pytest.mark.parametrize(
    "text,reason",
    (
        ("knowledge browse", Reason.MALFORMED_KNOWLEDGE_COMMAND),
        ("knowledge browse ::", Reason.MISSING_KNOWLEDGE_PAYLOAD),
        ("knowledge browse :: []", Reason.INVALID_KNOWLEDGE_JSON),
        ("knowledge browse :: null", Reason.INVALID_KNOWLEDGE_JSON),
        ("knowledge browse :: {} trailing", Reason.INVALID_KNOWLEDGE_JSON),
        ("knowledge browse :: {}{}", Reason.INVALID_KNOWLEDGE_JSON),
        ('knowledge browse :: {"workspace":"w"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge browse :: {"limit":50}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge browse :: {"key":"a","key":"b"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('knowledge find :: {"key":""}', Reason.INVALID_KNOWLEDGE_FIELDS),
    ),
)
def test_invalid_browse_remains_terminal(interpreter, workspace, text, reason):
    result = interpreter.interpret(text, workspace)
    assert result.status is Status.INVALID
    assert result.invalid_reason is reason
    assert result.intent is None


PYTHON_STRIP_WHITESPACE = (
    "\u0009\u000a\u000b\u000c\u000d\u001c\u001d\u001e\u001f\u0020"
    "\u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
)


@pytest.mark.parametrize(
    "prefix",
    (
        "knowledge browse-after :: ",
        " KnOwLeDgE BrOwSe-AfTeR ::",
        "knowledge\tbrowse-after\n::",
    ),
)
def test_browse_after_is_a_distinct_interpreted_intent(interpreter, workspace, prefix):
    result = interpreter.interpret(prefix + '{"after_record_id":"id"} \t\n', workspace)
    assert result == LocalCommandInterpretation(
        Status.INTERPRETED, BrowseAfterKnowledgeRecordsQuery("id")
    )
    assert type(result.intent) is BrowseAfterKnowledgeRecordsQuery


@pytest.mark.parametrize("whitespace", tuple(PYTHON_STRIP_WHITESPACE))
def test_browse_after_python_strip_and_interior_preservation(
    interpreter, workspace, whitespace
):
    anchor = "A" + whitespace + "  B"
    raw = whitespace + anchor + whitespace
    assert BrowseAfterKnowledgeRecordsQuery(raw).after_record_id == anchor
    result = interpreter.interpret(
        "knowledge browse-after :: " + json.dumps({"after_record_id": raw}), workspace
    )
    assert result.intent == BrowseAfterKnowledgeRecordsQuery(anchor)
    with pytest.raises(ValueError):
        BrowseAfterKnowledgeRecordsQuery(whitespace)
    assert interpreter.interpret(
        "knowledge browse-after :: " + json.dumps({"after_record_id": whitespace}),
        workspace,
    ).invalid_reason is Reason.INVALID_KNOWLEDGE_FIELDS


@pytest.mark.parametrize(
    "anchor",
    ("\u200b", "\ufeff", "\u200bID\ufeff", "AaZz", "\u00e9", "e\u0301",
     "\uff21", "\U0001f600", 'a"\\b\x00c'),
)
@pytest.mark.parametrize("ensure_ascii", (True, False))
def test_browse_after_preserves_unicode_and_json_escapes(
    interpreter, workspace, anchor, ensure_ascii
):
    assert BrowseAfterKnowledgeRecordsQuery(anchor).after_record_id == anchor
    payload = json.dumps({"after_record_id": anchor}, ensure_ascii=ensure_ascii)
    result = interpreter.interpret("knowledge browse-after :: " + payload, workspace)
    assert result.status is Status.INTERPRETED
    assert result.intent.after_record_id == anchor


@pytest.mark.parametrize("anchor", ("\ud800", "\udbff", "\udc00", "\udfff", "a\ud800b"))
def test_browse_after_rejects_isolated_surrogates_only_in_new_operation(
    interpreter, workspace, anchor
):
    with pytest.raises(ValueError, match="surrogates"):
        BrowseAfterKnowledgeRecordsQuery(anchor)
    # Both JSON escapes and a directly supplied Python string are validated.
    for ensure_ascii in (True, False):
        payload = json.dumps({"after_record_id": anchor}, ensure_ascii=ensure_ascii)
        result = interpreter.interpret(
            "knowledge browse-after :: " + payload, workspace
        )
        assert result == LocalCommandInterpretation(
            Status.INVALID, invalid_reason=Reason.INVALID_KNOWLEDGE_FIELDS
        )
    read = interpreter.interpret(
        "knowledge read :: " + json.dumps({"record_id": anchor}), workspace
    )
    store = interpreter.interpret(
        "knowledge store :: " + _store_payload(record_id=anchor), workspace
    )
    assert read.status is store.status is Status.INTERPRETED
    assert read.intent.record_id == store.intent.record.record_id == anchor


@pytest.mark.parametrize(
    "payload,reason",
    (
        ("", Reason.MISSING_KNOWLEDGE_PAYLOAD),
        ("{}", Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"record_id":"id"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"AFTER_RECORD_ID":"id"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":"id","workspace":"w"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":"id","actor":"a"}', Reason.INVALID_KNOWLEDGE_FIELDS),
        (
            '{"after_record_id":"a","after_record_id":"b"}',
            Reason.INVALID_KNOWLEDGE_FIELDS,
        ),
        ('{"after_record_id":null}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":1}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":true}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":[]}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":{}}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":""}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ('{"after_record_id":"   "}', Reason.INVALID_KNOWLEDGE_FIELDS),
        ("[]", Reason.INVALID_KNOWLEDGE_JSON),
        ("null", Reason.INVALID_KNOWLEDGE_JSON),
        ('"id"', Reason.INVALID_KNOWLEDGE_JSON),
        ('{"after_record_id":', Reason.INVALID_KNOWLEDGE_JSON),
        ('{"after_record_id":"id",}', Reason.INVALID_KNOWLEDGE_JSON),
        ('{"after_record_id":"id"} trailing', Reason.INVALID_KNOWLEDGE_JSON),
        ('{"after_record_id":"id"}{}', Reason.INVALID_KNOWLEDGE_JSON),
    ),
)
def test_browse_after_rejects_invalid_payloads(interpreter, workspace, payload, reason):
    result = interpreter.interpret("knowledge browse-after :: " + payload, workspace)
    assert result == LocalCommandInterpretation(Status.INVALID, invalid_reason=reason)


@pytest.mark.parametrize(
    "prefix",
    (
        "knowledge browse_after ::",
        "knowledge browseafter ::",
        "knowledge browse-afterx ::",
        "knowledge browse-after :",
        "knowledge browse-after",
        "knowledge browse-after::",
        "knowledge\u00a0browse-after ::",
        "knowledge brow\u017fe-after ::",
    ),
)
def test_browse_after_preserves_ascii_keyword_and_separator_rules(
    interpreter, workspace, prefix
):
    result = interpreter.interpret(prefix + ' {"after_record_id":"id"}', workspace)
    # Non-ASCII namespace whitespace remains outside the existing namespace.
    if "\u00a0" in prefix:
        assert result.status is Status.NOT_INTERPRETED
    else:
        assert result.invalid_reason is Reason.MALFORMED_KNOWLEDGE_COMMAND
    assert result.intent is None


def test_browse_after_query_is_closed_frozen_and_has_no_textual_size_cap():
    anchor = "\U0001f600" * 9000
    query = BrowseAfterKnowledgeRecordsQuery(anchor)
    assert query.after_record_id == anchor
    assert tuple(field.name for field in fields(query)) == ("after_record_id",)
    assert fields(BrowseKnowledgeRecordsQuery()) == ()
    with pytest.raises(FrozenInstanceError):
        query.after_record_id = "changed"
    with pytest.raises(TypeError):
        BrowseAfterKnowledgeRecordsQuery("id", workspace="w")
    with pytest.raises(TypeError):
        BrowseKnowledgeRecordsQuery(after_record_id="id")


@pytest.mark.parametrize("anchor", (None, 1, True, [], {}, "", " \t\n"))
def test_browse_after_direct_query_rejects_invalid_values(anchor):
    with pytest.raises(ValueError):
        BrowseAfterKnowledgeRecordsQuery(anchor)


def test_browse_after_query_requires_exact_string_type():
    class StringSubclass(str):
        pass

    with pytest.raises(ValueError):
        BrowseAfterKnowledgeRecordsQuery(StringSubclass("id"))


def test_browse_after_anchor_does_not_extend_initial_browse(interpreter, workspace):
    result = interpreter.interpret(
        'knowledge browse :: {"after_record_id":"id"}', workspace
    )
    assert result.invalid_reason is Reason.INVALID_KNOWLEDGE_FIELDS


def test_browse_after_port_is_separate_from_existing_repository_contracts():
    from app.cognition.local_resolution.contracts import (
        KnowledgeBrowseAfterRepository,
        KnowledgeBrowseRepository,
        KnowledgeRecordRepository,
    )

    assert tuple(signature(KnowledgeBrowseAfterRepository.browse_after).parameters) == (
        "self", "workspace", "after_record_id"
    )
    assert tuple(signature(KnowledgeBrowseRepository.browse).parameters) == (
        "self", "workspace"
    )
    assert "browse_after" not in KnowledgeBrowseRepository.__dict__
    assert "browse_after" not in KnowledgeRecordRepository.__dict__
