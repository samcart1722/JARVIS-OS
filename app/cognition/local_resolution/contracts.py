"""Infrastructure-free contracts for typed local resolution."""

from typing import Protocol

from app.cognition.local_resolution.models import (
    ActorIdentity,
    KnowledgeKind,
    KnowledgeRead,
    KnowledgeRecord,
    KnowledgeStored,
    ListItemsAdded,
    ListItemsSnapshot,
    WorkspaceIdentity,
)


class ListItemRepository(Protocol):
    def add(
        self, workspace: WorkspaceIdentity, list_id: str, items: tuple[str, ...]
    ) -> ListItemsAdded: ...

    def read(self, workspace: WorkspaceIdentity, list_id: str) -> ListItemsSnapshot: ...


class LocalRepositoryError(RuntimeError):
    """Safe repository failure without infrastructure detail."""


class KnowledgeRecordConflict(LocalRepositoryError):
    """Signal an immutable-record conflict without leaking storage details."""


class KnowledgeRecordRepository(Protocol):
    def store(self, record: KnowledgeRecord) -> KnowledgeStored: ...

    def read(self, workspace: WorkspaceIdentity, record_id: str) -> KnowledgeRead: ...

    def find_by_key(
        self,
        workspace: WorkspaceIdentity,
        key: str,
        kind: KnowledgeKind | None = None,
    ) -> tuple[KnowledgeRecord, ...]:
        """Return at most 51 exact matches ordered by binary record ID."""
        ...


class PermissionGrantRepositoryError(RuntimeError):
    """Signal a safe action-permission repository failure."""


class PermissionGrantConflict(PermissionGrantRepositoryError):
    """Signal an attempted duplicate exact action permission grant."""


class PermissionGrantRepository(Protocol):
    def is_granted(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool: ...

    def create(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> None: ...


class PermissionPolicy(Protocol):
    def is_allowed(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool: ...
