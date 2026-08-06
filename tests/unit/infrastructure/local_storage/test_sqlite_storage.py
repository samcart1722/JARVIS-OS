"""SQLite schema and durable repository behavior."""

import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.cognition.local_resolution.contracts import KnowledgeRecordConflict
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    FindKnowledgeRecordsQuery,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.infrastructure.local_storage.sqlite_storage import (
    SCHEMA_VERSION,
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
    UnsupportedSchemaVersion,
)


def _record(workspace: WorkspaceIdentity, value: str = "4") -> KnowledgeRecord:
    return KnowledgeRecord(
        "family.child.diaper-size",
        workspace,
        KnowledgeKind.FACT,
        "child.diaper_size",
        value,
        KnowledgeProvenance("user_asserted", "actor:wife"),
    )


def test_constructor_is_inert_and_initialization_is_explicit(tmp_path) -> None:
    path = tmp_path / "nested" / "local.sqlite3"
    storage = SQLiteLocalStorage(path)
    assert not path.exists() and not storage.is_open
    with pytest.raises(sqlite3.OperationalError):
        storage.open()
    assert not path.exists()


@pytest.mark.parametrize("invalid_path", ("", "   ", Path("."), "directory/"))
def test_constructor_rejects_paths_without_usable_filename(
    invalid_path, tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = tuple(tmp_path.iterdir())
    with pytest.raises(ValueError, match="filename"):
        SQLiteLocalStorage(invalid_path)
    assert tuple(tmp_path.iterdir()) == before


def test_valid_relative_filename_is_accepted_and_inert(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    storage = SQLiteLocalStorage("local.sqlite3")
    assert storage.database_path == Path("local.sqlite3")
    assert not storage.is_open
    assert tuple(tmp_path.iterdir()) == ()


def test_new_database_schema_version_and_idempotent_reopen(tmp_path) -> None:
    path = tmp_path / "local.sqlite3"
    first = SQLiteLocalStorage(path)
    try:
        first.open()
        first.initialize()
        assert first.is_open
    finally:
        first.close()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert connection.execute(
            "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (SCHEMA_VERSION,)
    second = SQLiteLocalStorage(path)
    try:
        second.open()
        second.initialize()
    finally:
        second.close()


def test_newer_schema_is_rejected_before_modification(tmp_path) -> None:
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        connection.execute("CREATE TABLE future_marker (value TEXT)")
    storage = SQLiteLocalStorage(path)
    try:
        storage.open()
        with pytest.raises(UnsupportedSchemaVersion):
            storage.initialize()
    finally:
        storage.close()
    with sqlite3.connect(path) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
            )
        }
    assert names == {"future_marker"}


def test_lists_persist_order_duplicates_isolation_and_snapshot(tmp_path) -> None:
    path = tmp_path / "lists.sqlite3"
    one, two = WorkspaceIdentity("one"), WorkspaceIdentity("two")
    first = SQLiteLocalStorage(path)
    try:
        first.open()
        first.initialize()
        added = first.add(one, "shopping", ("diapers", "Gerber", "grapes"))
        duplicate = first.add(one, "shopping", ("GRAPES", "milk"))
        snapshot = first.read(one, "shopping")
        first.add(one, "shopping", ("later",))
        first.add(one, "other'; DROP TABLE list_items; --", ("safe",))
        assert added.added == ("diapers", "Gerber", "grapes")
        assert duplicate.already_present == ("GRAPES",)
        assert snapshot.items == ("diapers", "Gerber", "grapes", "milk")
    finally:
        first.close()
    second = SQLiteLocalStorage(path)
    try:
        second.open()
        second.initialize()
        assert second.read(one, "shopping").items == (
            "diapers",
            "Gerber",
            "grapes",
            "milk",
            "later",
        )
        assert second.read(two, "shopping").items == ()
        assert second.read(one, "other'; DROP TABLE list_items; --").items == ("safe",)
    finally:
        second.close()


def test_knowledge_round_trip_idempotency_conflict_and_workspace_identity(
    tmp_path,
) -> None:
    path = tmp_path / "knowledge.sqlite3"
    one, two = WorkspaceIdentity("one"), WorkspaceIdentity("two")
    first = SQLiteLocalStorage(path)
    try:
        first.open()
        first.initialize()
        repository = SQLiteKnowledgeRecordRepository(first)
        record = _record(one)
        assert repository.store(record).created
        assert not repository.store(record).created
        with pytest.raises(KnowledgeRecordConflict):
            repository.store(_record(one, "5"))
        other_record = KnowledgeRecord(
            record.record_id,
            two,
            record.kind,
            record.key,
            "independent",
            record.provenance,
        )
        assert repository.store(other_record).created
    finally:
        first.close()
    second = SQLiteLocalStorage(path)
    try:
        second.open()
        second.initialize()
        repository = SQLiteKnowledgeRecordRepository(second)
        recovered = repository.read(one, record.record_id).record
        assert recovered == record
        assert recovered.provenance == record.provenance
        assert repository.read(two, record.record_id).record == other_record
        assert (
            repository.read(WorkspaceIdentity("three"), record.record_id).record is None
        )
        with pytest.raises(FrozenInstanceError):
            recovered.value = "changed"
    finally:
        second.close()


def test_knowledge_discovery_exact_binary_order_kind_workspace_and_cap(
    tmp_path,
) -> None:
    path = tmp_path / "discovery.sqlite3"
    one, two = WorkspaceIdentity("one"), WorkspaceIdentity("two")
    storage = SQLiteLocalStorage(path)
    storage.open()
    storage.initialize()
    repository = SQLiteKnowledgeRecordRepository(storage)

    def record(
        record_id, workspace=one, key="child.diaper_size", kind=KnowledgeKind.FACT
    ):
        return KnowledgeRecord(
            record_id,
            workspace,
            kind,
            key,
            "4",
            KnowledgeProvenance("user_asserted", f"actor:{record_id}"),
        )

    try:
        expected = tuple(sorted(("A", "r-10", "r-2", "z", "Á")))
        for record_id in reversed(expected):
            repository.store(record(record_id))
        repository.store(record("concept", kind=KnowledgeKind.CONCEPT))
        repository.store(record("substring", key="child.diaper"))
        repository.store(record("case", key="CHILD.DIAPER_SIZE"))
        repository.store(record("other", workspace=two))
        assert (
            tuple(
                item.record_id
                for item in repository.find_by_key(
                    one, "child.diaper_size", KnowledgeKind.FACT
                )
            )
            == expected
        )
        assert tuple(
            item.record_id
            for item in repository.find_by_key(
                one, "child.diaper_size", KnowledgeKind.CONCEPT
            )
        ) == ("concept",)
        assert repository.find_by_key(one, "missing") == ()
        assert all(
            item.workspace == one
            for item in repository.find_by_key(one, "child.diaper_size")
        )
        for number in range(60):
            repository.store(record(f"bulk-{number:02}", key="bulk"))
        assert len(repository.find_by_key(one, "bulk")) == 51
    finally:
        storage.close()

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND name NOT LIKE 'sqlite_autoindex_%'"
            )
        }
    assert tables == {"schema_metadata", "list_items", "knowledge_records"}
    assert indexes == set()


@pytest.mark.parametrize(
    ("total", "repository_count", "visible_count", "truncated"),
    (
        (49, 49, 49, False),
        (50, 50, 50, False),
        (51, 51, 50, True),
        (52, 51, 50, True),
    ),
)
def test_sqlite_discovery_boundary_matrix_through_real_capability(
    tmp_path, total, repository_count, visible_count, truncated
) -> None:
    storage = SQLiteLocalStorage(tmp_path / f"boundary-{total}.sqlite3")
    storage.open()
    storage.initialize()
    repository = SQLiteKnowledgeRecordRepository(storage)
    actor = ActorIdentity("actor")
    workspace, other = WorkspaceIdentity("home"), WorkspaceIdentity("other")

    def record(
        record_id,
        record_workspace=workspace,
        key="boundary.key",
        kind=KnowledgeKind.FACT,
    ):
        return KnowledgeRecord(
            record_id,
            record_workspace,
            kind,
            key,
            "value",
            KnowledgeProvenance("reviewed", f"actor:{record_id}"),
        )

    try:
        for number in reversed(range(total)):
            repository.store(record(f"match-{number:03}"))
        repository.store(record("other-key", key="boundary"))
        repository.store(record("other-kind", kind=KnowledgeKind.CONCEPT))
        repository.store(record("other-workspace", record_workspace=other))

        repository_records = repository.find_by_key(
            workspace, "boundary.key", KnowledgeKind.FACT
        )
        policy = ExplicitPermissionPolicy(
            (
                PermissionGrant(
                    actor.actor_id,
                    workspace.workspace_id,
                    frozenset((KNOWLEDGE_RECORDS_READ,)),
                ),
            )
        )
        result = StructuredKnowledgeCapability(repository, policy).execute(
            actor,
            workspace,
            FindKnowledgeRecordsQuery("boundary.key", KnowledgeKind.FACT),
        )

        expected_ids = tuple(f"match-{number:03}" for number in range(total))
        assert len(repository_records) == repository_count <= 51
        assert (
            tuple(record.record_id for record in repository_records)
            == expected_ids[:51]
        )
        assert len(result.records) == visible_count <= 50
        assert tuple(record.record_id for record in result.records) == expected_ids[:50]
        assert result.truncated is truncated
        assert all(
            item.workspace == workspace
            and item.key == "boundary.key"
            and item.kind is KnowledgeKind.FACT
            for item in (*repository_records, *result.records)
        )
    finally:
        storage.close()
