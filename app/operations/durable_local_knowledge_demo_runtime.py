"""Explicit operational composition for durable local list and knowledge proof."""

from dataclasses import dataclass
from pathlib import Path

from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    PermissionGrant,
)
from app.core.config import Settings
from app.core.container import Container
from app.infrastructure.local_storage.sqlite_storage import (
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
)

WORKSPACE_ID = "family-home"
OTHER_WORKSPACE_ID = "family-away"
AUTHORIZED_ACTOR_ID = "wife"
DENIED_ACTOR_ID = "guest"
LIST_ID = "shopping"
RECORD_ID = "family.child.diaper-size"
EXPECTED_LIST = ("diapers", "Gerber", "grapes", "milk")


@dataclass(frozen=True, slots=True)
class DurableLocalKnowledgeDemoReport:
    phase: str
    list_items: tuple[str, ...]
    provenance: KnowledgeProvenance
    duplicate_preserved: bool
    workspace_isolated: bool
    denied_read: bool
    denied_mutation: bool
    model_calls: int = 0
    external_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    def __post_init__(self) -> None:
        if self.phase not in {"seed", "verify"}:
            raise ValueError("Unknown durable demo phase.")
        if any(
            count != 0
            for count in (
                self.model_calls,
                self.external_calls,
                self.readiness_calls,
                self.network_calls,
            )
        ):
            raise ValueError("Durable local demo cannot include remote calls.")


def _record(workspace: WorkspaceIdentity) -> KnowledgeRecord:
    return KnowledgeRecord(
        RECORD_ID,
        workspace,
        KnowledgeKind.FACT,
        "child.diaper_size",
        "4",
        KnowledgeProvenance("user_asserted", "actor:wife"),
    )


def _container(storage: SQLiteLocalStorage) -> Container:
    actions = frozenset(
        (
            LIST_ITEMS_ADD,
            LIST_ITEMS_READ,
            KNOWLEDGE_RECORDS_ADD,
            KNOWLEDGE_RECORDS_READ,
        )
    )
    grant = PermissionGrant(AUTHORIZED_ACTOR_ID, WORKSPACE_ID, actions)
    isolation_grant = PermissionGrant(
        AUTHORIZED_ACTOR_ID,
        OTHER_WORKSPACE_ID,
        frozenset((LIST_ITEMS_READ, KNOWLEDGE_RECORDS_READ)),
    )
    return Container(
        Settings(_env_file=None),
        local_permission_grants=(grant, isolation_grant),
        local_list_repository=storage,
        local_knowledge_repository=SQLiteKnowledgeRecordRepository(storage),
    )


def seed_durable_local_knowledge(
    database_path: str | Path,
) -> DurableLocalKnowledgeDemoReport:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    storage = SQLiteLocalStorage(path)
    try:
        storage.open()
        storage.initialize()
        resolver = _container(storage).local_first_resolver
        actor = ActorIdentity(AUTHORIZED_ACTOR_ID)
        workspace = WorkspaceIdentity(WORKSPACE_ID)
        first = resolver.resolve(
            actor,
            workspace,
            AddListItemsCommand(LIST_ID, ("diapers", "Gerber", "grapes")),
        )
        second = resolver.resolve(
            actor,
            workspace,
            AddListItemsCommand(LIST_ID, ("GRAPES", "milk")),
        )
        stored = resolver.resolve(
            actor, workspace, StoreKnowledgeRecordCommand(_record(workspace))
        )
        final = resolver.resolve(actor, workspace, ReadListItemsQuery(LIST_ID))
        if not (first.success and second.success and stored.success and final.success):
            raise RuntimeError("Durable local seed was incomplete.")
        if final.items != EXPECTED_LIST or second.already_present != ("GRAPES",):
            raise RuntimeError("Durable list seed did not match expected state.")
        return DurableLocalKnowledgeDemoReport(
            "seed",
            final.items,
            stored.record.provenance,
            True,
            False,
            False,
            False,
        )
    finally:
        storage.close()


def verify_durable_local_knowledge(
    database_path: str | Path,
) -> DurableLocalKnowledgeDemoReport:
    path = Path(database_path)
    if not path.is_file():
        raise RuntimeError("Durable local database is unavailable.")
    storage = SQLiteLocalStorage(path)
    try:
        storage.open()
        storage.initialize()
        resolver = _container(storage).local_first_resolver
        actor = ActorIdentity(AUTHORIZED_ACTOR_ID)
        denied = ActorIdentity(DENIED_ACTOR_ID)
        workspace = WorkspaceIdentity(WORKSPACE_ID)
        other = WorkspaceIdentity(OTHER_WORKSPACE_ID)
        list_result = resolver.resolve(actor, workspace, ReadListItemsQuery(LIST_ID))
        record_result = resolver.resolve(
            actor, workspace, ReadKnowledgeRecordQuery(RECORD_ID)
        )
        other_list = resolver.resolve(actor, other, ReadListItemsQuery(LIST_ID))
        other_record = resolver.resolve(
            actor, other, ReadKnowledgeRecordQuery(RECORD_ID)
        )
        denied_list = resolver.resolve(denied, workspace, ReadListItemsQuery(LIST_ID))
        denied_record = resolver.resolve(
            denied, workspace, ReadKnowledgeRecordQuery(RECORD_ID)
        )
        denied_write = resolver.resolve(
            denied,
            workspace,
            AddListItemsCommand(LIST_ID, ("forbidden",)),
        )
        denied_knowledge_write = resolver.resolve(
            denied, workspace, StoreKnowledgeRecordCommand(_record(workspace))
        )
        unchanged = resolver.resolve(actor, workspace, ReadListItemsQuery(LIST_ID))
        workspace_isolated = (
            other_list.success
            and other_list.items == ()
            and not other_record.success
        )
        denied_read = not denied_list.success and not denied_record.success
        denied_mutation = (
            not denied_write.success
            and not denied_knowledge_write.success
            and unchanged.items == EXPECTED_LIST
        )
        if not (
            list_result.success
            and list_result.items == EXPECTED_LIST
            and record_result.success
            and record_result.record == _record(workspace)
            and workspace_isolated
            and denied_read
            and denied_mutation
        ):
            raise RuntimeError("Durable local verification was incomplete.")
        return DurableLocalKnowledgeDemoReport(
            "verify",
            list_result.items,
            record_result.record.provenance,
            True,
            workspace_isolated,
            denied_read,
            denied_mutation,
        )
    finally:
        storage.close()
