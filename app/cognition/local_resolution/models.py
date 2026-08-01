"""Immutable inputs and outcomes for typed local resolution."""

from dataclasses import dataclass
from enum import Enum

LOCAL_CAPABILITY_ROUTE = "local_capability"
LOCAL_NOT_HANDLED_ROUTE = "not_handled"
LOCAL_PERMISSION_DENIED = "local_permission_denied"
LOCAL_VALIDATION_FAILED = "local_validation_failed"
LOCAL_KNOWLEDGE_CONFLICT = "local_knowledge_conflict"
LOCAL_KNOWLEDGE_NOT_FOUND = "local_knowledge_not_found"


def _non_blank(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value.strip()


@dataclass(frozen=True, slots=True)
class ActorIdentity:
    actor_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "actor_id", _non_blank(self.actor_id, "Actor ID"))


@dataclass(frozen=True, slots=True)
class WorkspaceIdentity:
    workspace_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "workspace_id", _non_blank(self.workspace_id, "Workspace ID")
        )


@dataclass(frozen=True, slots=True)
class AddListItemsCommand:
    list_id: str
    items: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "list_id", _non_blank(self.list_id, "List ID"))
        if not isinstance(self.items, tuple) or not self.items:
            raise ValueError("Items must be a non-empty tuple.")
        object.__setattr__(
            self,
            "items",
            tuple(_non_blank(item, "Item") for item in self.items),
        )


@dataclass(frozen=True, slots=True)
class ReadListItemsQuery:
    list_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "list_id", _non_blank(self.list_id, "List ID"))


@dataclass(frozen=True, slots=True)
class ListItemsSnapshot:
    items: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ListItemsAdded:
    added: tuple[str, ...]
    already_present: tuple[str, ...]
    items: tuple[str, ...]


class KnowledgeKind(str, Enum):
    FACT = "fact"
    CONCEPT = "concept"
    STATE = "state"


@dataclass(frozen=True, slots=True)
class KnowledgeProvenance:
    source_type: str
    source_reference: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_type", _non_blank(self.source_type, "Source type")
        )
        object.__setattr__(
            self,
            "source_reference",
            _non_blank(self.source_reference, "Source reference"),
        )


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    record_id: str
    workspace: WorkspaceIdentity
    kind: KnowledgeKind
    key: str
    value: str
    provenance: KnowledgeProvenance

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _non_blank(self.record_id, "Record ID"))
        if not isinstance(self.workspace, WorkspaceIdentity):
            raise ValueError("Knowledge workspace must be explicit.")
        if not isinstance(self.kind, KnowledgeKind):
            raise ValueError("Knowledge kind is invalid.")
        object.__setattr__(self, "key", _non_blank(self.key, "Knowledge key"))
        object.__setattr__(self, "value", _non_blank(self.value, "Knowledge value"))
        if not isinstance(self.provenance, KnowledgeProvenance):
            raise ValueError("Knowledge provenance is required.")


@dataclass(frozen=True, slots=True)
class StoreKnowledgeRecordCommand:
    record: KnowledgeRecord

    def __post_init__(self) -> None:
        if not isinstance(self.record, KnowledgeRecord):
            raise ValueError("A valid knowledge record is required.")


@dataclass(frozen=True, slots=True)
class ReadKnowledgeRecordQuery:
    record_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _non_blank(self.record_id, "Record ID"))


@dataclass(frozen=True, slots=True)
class KnowledgeStored:
    record: KnowledgeRecord
    created: bool


@dataclass(frozen=True, slots=True)
class KnowledgeRead:
    record: KnowledgeRecord | None


@dataclass(frozen=True, slots=True)
class LocalResolutionResult:
    handled: bool
    success: bool
    response: str
    resolution_route: str
    model_used: bool = False
    external_access: bool = False
    added: tuple[str, ...] = ()
    already_present: tuple[str, ...] = ()
    items: tuple[str, ...] = ()
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.model_used or self.external_access:
            raise ValueError("Local resolution cannot report remote activity.")
        if not self.handled and (
            self.success or self.resolution_route != LOCAL_NOT_HANDLED_ROUTE
        ):
            raise ValueError("Not-handled local result is inconsistent.")


@dataclass(frozen=True, slots=True)
class KnowledgeResolutionResult:
    handled: bool
    success: bool
    response: str
    resolution_route: str
    record: KnowledgeRecord | None = None
    created: bool = False
    error_code: str | None = None
    model_used: bool = False
    external_access: bool = False

    def __post_init__(self) -> None:
        if not self.handled or self.resolution_route != LOCAL_CAPABILITY_ROUTE:
            raise ValueError("Knowledge result must be a handled local result.")
        if self.model_used or self.external_access:
            raise ValueError("Local resolution cannot report remote activity.")
        if self.success != (self.record is not None):
            raise ValueError("Knowledge result success and record are inconsistent.")
        if self.created and not self.success:
            raise ValueError("Only a successful store can create a record.")
