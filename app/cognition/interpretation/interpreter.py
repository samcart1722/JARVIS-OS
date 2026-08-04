"""Deterministic interpreter for deliberately narrow local command grammars."""

import json
import re

from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.local_resolution.models import (
    AddListItemsCommand,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)

_LIST_NAMESPACE = re.compile(r"^list(?:\s|$)", re.IGNORECASE | re.ASCII)
_KNOWLEDGE_NAMESPACE = re.compile(
    r"^knowledge(?:\s|$)", re.IGNORECASE | re.ASCII
)
_KNOWLEDGE_PREFIX = re.compile(
    r"^knowledge\s+(read|store)\s+::", re.IGNORECASE | re.ASCII
)
_READ_FIELDS = frozenset(("record_id",))
_STORE_FIELDS = frozenset(
    ("record_id", "kind", "key", "value", "source_type", "source_reference")
)


class _DuplicateJsonKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey
        result[key] = value
    return result


def _invalid(reason: LocalCommandInvalidReason) -> LocalCommandInterpretation:
    return LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INVALID, invalid_reason=reason
    )


class DeterministicLocalCommandInterpreter:
    def interpret(
        self, text: str, workspace: WorkspaceIdentity
    ) -> LocalCommandInterpretation:
        if not isinstance(text, str) or not text.strip():
            return _invalid(LocalCommandInvalidReason.INVALID_INPUT)
        command = text.strip()
        if _KNOWLEDGE_NAMESPACE.match(command):
            return self._interpret_knowledge(command, workspace)
        if not _LIST_NAMESPACE.match(command):
            return LocalCommandInterpretation(
                LocalCommandInterpretationStatus.NOT_INTERPRETED
            )

        tokens = command.split(None, 2)
        if len(tokens) < 2:
            return _invalid(LocalCommandInvalidReason.MALFORMED_LIST_COMMAND)
        operation = tokens[1].lower()
        remainder = tokens[2] if len(tokens) == 3 else ""
        if operation == "read":
            if not remainder:
                return _invalid(LocalCommandInvalidReason.MISSING_LIST_ID)
            if len(remainder.split()) != 1:
                return _invalid(LocalCommandInvalidReason.MALFORMED_LIST_COMMAND)
            return LocalCommandInterpretation(
                LocalCommandInterpretationStatus.INTERPRETED,
                intent=ReadListItemsQuery(remainder),
            )
        if operation != "add":
            return _invalid(LocalCommandInvalidReason.MALFORMED_LIST_COMMAND)
        if "::" not in remainder:
            if not remainder:
                return _invalid(LocalCommandInvalidReason.MISSING_LIST_ID)
            return _invalid(LocalCommandInvalidReason.MALFORMED_LIST_COMMAND)
        list_part, item_part = remainder.split("::", 1)
        list_id = list_part.strip()
        if not list_id:
            return _invalid(LocalCommandInvalidReason.MISSING_LIST_ID)
        if len(list_id.split()) != 1:
            return _invalid(LocalCommandInvalidReason.MALFORMED_LIST_COMMAND)
        if not item_part.strip():
            return _invalid(LocalCommandInvalidReason.MISSING_ITEMS)
        items = tuple(item.strip() for item in item_part.split("|"))
        if any(not item for item in items):
            return _invalid(LocalCommandInvalidReason.EMPTY_ITEM)
        return LocalCommandInterpretation(
            LocalCommandInterpretationStatus.INTERPRETED,
            intent=AddListItemsCommand(list_id, items),
        )

    def _interpret_knowledge(
        self, command: str, workspace: WorkspaceIdentity
    ) -> LocalCommandInterpretation:
        prefix = _KNOWLEDGE_PREFIX.match(command)
        if prefix is None:
            return _invalid(
                LocalCommandInvalidReason.MALFORMED_KNOWLEDGE_COMMAND
            )
        payload_text = command[prefix.end() :].lstrip()
        if not payload_text:
            return _invalid(LocalCommandInvalidReason.MISSING_KNOWLEDGE_PAYLOAD)
        try:
            decoder = json.JSONDecoder(object_pairs_hook=_unique_object)
            payload, end = decoder.raw_decode(payload_text)
        except _DuplicateJsonKey:
            return _invalid(LocalCommandInvalidReason.INVALID_KNOWLEDGE_FIELDS)
        except (json.JSONDecodeError, TypeError, ValueError):
            return _invalid(LocalCommandInvalidReason.INVALID_KNOWLEDGE_JSON)
        if payload_text[end:].strip() or not isinstance(payload, dict):
            return _invalid(LocalCommandInvalidReason.INVALID_KNOWLEDGE_JSON)

        operation = prefix.group(1).lower()
        required = _READ_FIELDS if operation == "read" else _STORE_FIELDS
        if (
            frozenset(payload) != required
            or any(not isinstance(value, str) for value in payload.values())
            or any(not value.strip() for value in payload.values())
        ):
            return _invalid(LocalCommandInvalidReason.INVALID_KNOWLEDGE_FIELDS)
        if operation == "read":
            return LocalCommandInterpretation(
                LocalCommandInterpretationStatus.INTERPRETED,
                intent=ReadKnowledgeRecordQuery(payload["record_id"]),
            )
        try:
            kind = KnowledgeKind(payload["kind"])
        except ValueError:
            return _invalid(LocalCommandInvalidReason.INVALID_KNOWLEDGE_KIND)
        try:
            record = KnowledgeRecord(
                payload["record_id"],
                workspace,
                kind,
                payload["key"],
                payload["value"],
                KnowledgeProvenance(
                    payload["source_type"], payload["source_reference"]
                ),
            )
        except (TypeError, ValueError):
            return _invalid(LocalCommandInvalidReason.INVALID_KNOWLEDGE_FIELDS)
        return LocalCommandInterpretation(
            LocalCommandInterpretationStatus.INTERPRETED,
            intent=StoreKnowledgeRecordCommand(record),
        )
