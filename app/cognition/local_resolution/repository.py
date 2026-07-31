"""Process-local, workspace-scoped structured-list repository."""

from app.cognition.local_resolution.models import (
    ListItemsAdded,
    ListItemsSnapshot,
    WorkspaceIdentity,
)


class InMemoryListItemRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], list[str]] = {}

    def add(
        self, workspace: WorkspaceIdentity, list_id: str, items: tuple[str, ...]
    ) -> ListItemsAdded:
        if not isinstance(workspace, WorkspaceIdentity) or not list_id.strip():
            raise ValueError("Valid workspace and list ID are required.")
        normalized_items = tuple(item.strip() for item in items)
        if any(not item for item in normalized_items):
            raise ValueError("List item cannot be empty.")
        current = self._items.setdefault((workspace.workspace_id, list_id), [])
        accepted_keys = {item.casefold() for item in current}
        added: list[str] = []
        duplicates: list[str] = []
        for normalized in normalized_items:
            key = normalized.casefold()
            if key in accepted_keys:
                duplicates.append(normalized)
            else:
                current.append(normalized)
                accepted_keys.add(key)
                added.append(normalized)
        return ListItemsAdded(tuple(added), tuple(duplicates), tuple(current))

    def read(self, workspace: WorkspaceIdentity, list_id: str) -> ListItemsSnapshot:
        if not isinstance(workspace, WorkspaceIdentity) or not list_id.strip():
            raise ValueError("Valid workspace and list ID are required.")
        return ListItemsSnapshot(
            tuple(self._items.get((workspace.workspace_id, list_id), ()))
        )
