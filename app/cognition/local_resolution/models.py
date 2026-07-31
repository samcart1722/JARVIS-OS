"""Immutable inputs and outcomes for typed local resolution."""

from dataclasses import dataclass

LOCAL_CAPABILITY_ROUTE = "local_capability"
LOCAL_NOT_HANDLED_ROUTE = "not_handled"
LOCAL_PERMISSION_DENIED = "local_permission_denied"
LOCAL_VALIDATION_FAILED = "local_validation_failed"


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
