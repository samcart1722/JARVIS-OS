"""Immutable values at the deterministic text interpretation boundary."""

from dataclasses import dataclass
from enum import Enum

from app.cognition.local_resolution.models import (
    AddListItemsCommand,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
)

LocalCommandIntent = (
    AddListItemsCommand
    | ReadListItemsQuery
    | StoreKnowledgeRecordCommand
    | ReadKnowledgeRecordQuery
)


class LocalCommandInterpretationStatus(str, Enum):
    INTERPRETED = "interpreted"
    NOT_INTERPRETED = "not_interpreted"
    INVALID = "invalid"


class LocalCommandInvalidReason(str, Enum):
    INVALID_INPUT = "invalid_input"
    MALFORMED_LIST_COMMAND = "malformed_list_command"
    MISSING_LIST_ID = "missing_list_id"
    MISSING_ITEMS = "missing_items"
    EMPTY_ITEM = "empty_item"
    MALFORMED_KNOWLEDGE_COMMAND = "malformed_knowledge_command"
    MISSING_KNOWLEDGE_PAYLOAD = "missing_knowledge_payload"
    INVALID_KNOWLEDGE_JSON = "invalid_knowledge_json"
    INVALID_KNOWLEDGE_FIELDS = "invalid_knowledge_fields"
    INVALID_KNOWLEDGE_KIND = "invalid_knowledge_kind"


@dataclass(frozen=True, slots=True)
class LocalCommandInterpretation:
    status: LocalCommandInterpretationStatus
    intent: LocalCommandIntent | None = None
    invalid_reason: LocalCommandInvalidReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, LocalCommandInterpretationStatus):
            raise ValueError("Interpretation status is invalid.")
        if self.status is LocalCommandInterpretationStatus.INTERPRETED:
            if not isinstance(
                self.intent,
                (
                    AddListItemsCommand,
                    ReadListItemsQuery,
                    StoreKnowledgeRecordCommand,
                    ReadKnowledgeRecordQuery,
                ),
            ):
                raise ValueError("An interpreted result requires a typed local intent.")
            if self.invalid_reason is not None:
                raise ValueError("An interpreted result cannot have an invalid reason.")
            return
        if self.intent is not None:
            raise ValueError("Only an interpreted result can contain an intent.")
        if self.status is LocalCommandInterpretationStatus.INVALID:
            if not isinstance(self.invalid_reason, LocalCommandInvalidReason):
                raise ValueError("An invalid result requires a stable reason.")
        elif self.invalid_reason is not None:
            raise ValueError("A not-interpreted result cannot have an invalid reason.")


@dataclass(frozen=True, slots=True)
class UnrecognizedLocalIntent:
    """Sentinel passed through local resolution for unrecognized text."""


UNRECOGNIZED_LOCAL_INTENT = UnrecognizedLocalIntent()
