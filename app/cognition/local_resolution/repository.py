"""Process-local, workspace-scoped list and knowledge repositories."""

from app.cognition.local_resolution.models import (
    KNOWLEDGE_DISCOVERY_LOOKAHEAD,
    KnowledgeKind,
    KnowledgeRead,
    KnowledgeRecord,
    KnowledgeStored,
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


class InMemoryKnowledgeRecordRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], KnowledgeRecord] = {}

    def store(self, record: KnowledgeRecord) -> KnowledgeStored:
        from app.cognition.local_resolution.contracts import KnowledgeRecordConflict

        if not isinstance(record, KnowledgeRecord):
            raise ValueError("A valid knowledge record is required.")
        identity = (record.workspace.workspace_id, record.record_id)
        existing = self._records.get(identity)
        if existing is None:
            self._records[identity] = record
            return KnowledgeStored(record, True)
        if existing == record:
            return KnowledgeStored(existing, False)
        raise KnowledgeRecordConflict("Knowledge record already exists.")

    def read(self, workspace: WorkspaceIdentity, record_id: str) -> KnowledgeRead:
        if not isinstance(workspace, WorkspaceIdentity) or not record_id.strip():
            raise ValueError("Valid workspace and record ID are required.")
        return KnowledgeRead(self._records.get((workspace.workspace_id, record_id)))

    def find_by_key(
        self,
        workspace: WorkspaceIdentity,
        key: str,
        kind: KnowledgeKind | None = None,
    ) -> tuple[KnowledgeRecord, ...]:
        if (
            not isinstance(workspace, WorkspaceIdentity)
            or not isinstance(key, str)
            or not key.strip()
        ):
            raise ValueError("Valid workspace and knowledge key are required.")
        if kind is not None and not isinstance(kind, KnowledgeKind):
            raise ValueError("Knowledge kind is invalid.")
        matches = (
            record
            for (workspace_id, _), record in self._records.items()
            if workspace_id == workspace.workspace_id
            and record.key == key.strip()
            and (kind is None or record.kind is kind)
        )
        return tuple(
            sorted(matches, key=lambda record: record.record_id)[
                :KNOWLEDGE_DISCOVERY_LOOKAHEAD
            ]
        )
