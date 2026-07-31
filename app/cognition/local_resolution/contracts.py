"""Infrastructure-free contracts for local list resolution."""

from typing import Protocol

from app.cognition.local_resolution.models import (
    ActorIdentity,
    ListItemsAdded,
    ListItemsSnapshot,
    WorkspaceIdentity,
)


class ListItemRepository(Protocol):
    def add(
        self, workspace: WorkspaceIdentity, list_id: str, items: tuple[str, ...]
    ) -> ListItemsAdded: ...

    def read(self, workspace: WorkspaceIdentity, list_id: str) -> ListItemsSnapshot: ...


class PermissionPolicy(Protocol):
    def is_allowed(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool: ...
