"""Generic structured-list capability with authorization before access."""

from app.cognition.local_resolution.contracts import (
    ListItemRepository,
    PermissionPolicy,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    ListItemsAdded,
    ListItemsSnapshot,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import LIST_ITEMS_ADD, LIST_ITEMS_READ


class LocalPermissionDenied(PermissionError):
    """Signal a safe local denial without exposing repository state."""


class StructuredListCapability:
    def __init__(
        self, repository: ListItemRepository, permissions: PermissionPolicy
    ) -> None:
        self._repository = repository
        self._permissions = permissions

    def execute(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        intent: AddListItemsCommand | ReadListItemsQuery,
    ) -> ListItemsAdded | ListItemsSnapshot:
        if isinstance(intent, AddListItemsCommand):
            action = LIST_ITEMS_ADD
        elif isinstance(intent, ReadListItemsQuery):
            action = LIST_ITEMS_READ
        else:
            raise TypeError("Unsupported local intent.")
        if not self._permissions.is_allowed(actor, workspace, action):
            raise LocalPermissionDenied("Local operation is not authorized.")
        if isinstance(intent, AddListItemsCommand):
            return self._repository.add(workspace, intent.list_id, intent.items)
        if isinstance(intent, ReadListItemsQuery):
            return self._repository.read(workspace, intent.list_id)
        raise TypeError("Unsupported local intent.")
