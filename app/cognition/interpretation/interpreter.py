"""Deterministic interpreter for the deliberately narrow list grammar."""

import re

from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.local_resolution.models import (
    AddListItemsCommand,
    ReadListItemsQuery,
)

_LIST_NAMESPACE = re.compile(r"^list(?:\s|$)", re.IGNORECASE | re.ASCII)


def _invalid(reason: LocalCommandInvalidReason) -> LocalCommandInterpretation:
    return LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INVALID, invalid_reason=reason
    )


class DeterministicLocalCommandInterpreter:
    def interpret(self, text: str) -> LocalCommandInterpretation:
        if not isinstance(text, str) or not text.strip():
            return _invalid(LocalCommandInvalidReason.INVALID_INPUT)
        command = text.strip()
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
