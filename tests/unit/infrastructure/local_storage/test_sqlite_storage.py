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
    LocalStorageError,
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
    UnsupportedSchemaVersion,
)
from app.membership import (
    InMemoryMembershipRepository,
    MembershipRepositoryError,
    MembershipStatus,
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


def _create_v1_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE schema_metadata ("
            "schema_key TEXT PRIMARY KEY, schema_version INTEGER NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE list_items ("
            "workspace_id TEXT NOT NULL, list_id TEXT NOT NULL, "
            "normalized_item TEXT NOT NULL, display_item TEXT NOT NULL, "
            "position INTEGER NOT NULL, "
            "PRIMARY KEY (workspace_id, list_id, normalized_item), "
            "UNIQUE (workspace_id, list_id, position))"
        )
        connection.execute(
            "CREATE TABLE knowledge_records ("
            "workspace_id TEXT NOT NULL, record_id TEXT NOT NULL, "
            "kind TEXT NOT NULL, knowledge_key TEXT NOT NULL, "
            "knowledge_value TEXT NOT NULL, source_type TEXT NOT NULL, "
            "source_reference TEXT NOT NULL, "
            "PRIMARY KEY (workspace_id, record_id))"
        )
        connection.execute(
            "INSERT INTO schema_metadata VALUES ('local_storage', 1)"
        )
        connection.execute("PRAGMA user_version = 1")


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
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
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
    assert tables == {
        "schema_metadata",
        "list_items",
        "knowledge_records",
        "actor_workspace_memberships",
        "principal_actor_mappings",
    }
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


def test_fresh_v3_schema_contains_approved_membership_and_mapping_shapes(
    tmp_path,
) -> None:
    path = tmp_path / "fresh.sqlite3"
    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("workspace")
        assert storage.create(actor, workspace).status is MembershipStatus.ACTIVE
        assert storage.read(workspace, "list").items == ()
        assert storage.read_knowledge(workspace, "record").record is None

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        assert connection.execute(
            "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (SCHEMA_VERSION,)
        columns = connection.execute(
            "PRAGMA table_info(actor_workspace_memberships)"
        ).fetchall()
        assert tuple((row[1], row[2], row[3], row[5]) for row in columns) == (
            ("actor_id", "TEXT", 1, 1),
            ("workspace_id", "TEXT", 1, 2),
            ("status", "TEXT", 1, 0),
        )
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = ?",
            ("actor_workspace_memberships",),
        ).fetchone()[0]
        assert "status IN ('active', 'inactive')" in sql

        mapping_columns = connection.execute(
            "PRAGMA table_info(principal_actor_mappings)"
        ).fetchall()

        assert tuple(
            (row[1], row[2], row[3], row[5])
            for row in mapping_columns
        ) == (
            ("principal_id", "TEXT", 1, 1),
            ("actor_id", "TEXT", 1, 0),
        )

        mapping_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = ?",
            ("principal_actor_mappings",),
        ).fetchone()[0]

        normalized_mapping_sql = " ".join(
            mapping_sql.split()
        ).lower()

        assert (
            "principal_id text not null collate binary primary key"
            in normalized_mapping_sql
        )
        assert "actor_id text not null" in normalized_mapping_sql
        assert "unique (actor_id)" not in normalized_mapping_sql


def test_v1_migration_is_additive_and_preserves_semantic_values(tmp_path) -> None:
    path = tmp_path / "migration.sqlite3"
    _create_v1_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO list_items VALUES (?, ?, ?, ?, ?)",
            ("home", "shopping", "milk", "Milk", 0),
        )
        connection.execute(
            "INSERT INTO knowledge_records VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("home", "record", "fact", "family.value", "exact", "reviewed", "source"),
        )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        workspace = WorkspaceIdentity("home")
        assert storage.read(workspace, "shopping").items == ("Milk",)
        recovered = storage.read_knowledge(workspace, "record").record
        assert recovered is not None
        assert (recovered.key, recovered.value) == ("family.value", "exact")

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        assert connection.execute(
            "SELECT workspace_id, list_id, normalized_item, display_item, position "
            "FROM list_items"
        ).fetchone() == ("home", "shopping", "milk", "Milk", 0)
        assert connection.execute(
            "SELECT workspace_id, record_id, kind, knowledge_key, knowledge_value, "
            "source_type, source_reference FROM knowledge_records"
        ).fetchone() == (
            "home", "record", "fact", "family.value", "exact", "reviewed", "source"
        )


def test_v1_migration_failure_rolls_back_ddl_versions_and_preserves_data(
    tmp_path,
) -> None:
    path = tmp_path / "migration-failure.sqlite3"
    _create_v1_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO list_items VALUES (?, ?, ?, ?, ?)",
            ("home", "shopping", "milk", "Milk", 0),
        )
        connection.execute(
            "INSERT INTO knowledge_records VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("home", "record", "fact", "family.value", "exact", "reviewed", "source"),
        )
        connection.execute(
            "CREATE TRIGGER fail_schema_metadata_update "
            "BEFORE UPDATE ON schema_metadata BEGIN "
            "SELECT RAISE(ABORT, 'forced migration failure'); END"
        )

    with SQLiteLocalStorage(path) as storage:
        with pytest.raises(LocalStorageError, match="migration failed"):
            storage.initialize()

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute(
            "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (1,)
        assert connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("actor_workspace_memberships",),
        ).fetchone() == (0,)
        assert connection.execute("SELECT * FROM list_items").fetchone() == (
            "home", "shopping", "milk", "Milk", 0
        )
        assert connection.execute("SELECT * FROM knowledge_records").fetchone() == (
            "home", "record", "fact", "family.value", "exact", "reviewed", "source"
        )
        connection.execute("DROP TRIGGER fail_schema_metadata_update")

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        assert storage.read(WorkspaceIdentity("home"), "shopping").items == ("Milk",)
        assert storage.read_knowledge(
            WorkspaceIdentity("home"), "record"
        ).record.value == "exact"
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        assert connection.execute(
            "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (SCHEMA_VERSION,)
        assert connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table' AND name = ?",
            ("actor_workspace_memberships",),
        ).fetchone() == (1,)


@pytest.mark.parametrize("repository_kind", ("memory", "sqlite"))
def test_membership_repository_lifecycle_parity(repository_kind, tmp_path) -> None:
    storage = None
    if repository_kind == "memory":
        repository = InMemoryMembershipRepository()
    else:
        storage = SQLiteLocalStorage(tmp_path / "parity.sqlite3")
        storage.open()
        storage.initialize()
        repository = storage
    actor, other_actor = ActorIdentity("Actor"), ActorIdentity("actor")
    workspace, other_workspace = WorkspaceIdentity("Home"), WorkspaceIdentity("home")
    try:
        assert repository.get(actor, workspace) is None
        assert repository.activate(actor, workspace) is None
        assert repository.deactivate(actor, workspace) is None
        assert repository.create(actor, workspace).status is MembershipStatus.ACTIVE
        assert repository.create(actor, workspace).status is MembershipStatus.ACTIVE
        assert (
            repository.deactivate(actor, workspace).status
            is MembershipStatus.INACTIVE
        )
        assert (
            repository.deactivate(actor, workspace).status
            is MembershipStatus.INACTIVE
        )
        assert repository.create(actor, workspace).status is MembershipStatus.INACTIVE
        assert repository.activate(actor, workspace).status is MembershipStatus.ACTIVE
        assert repository.activate(actor, workspace).status is MembershipStatus.ACTIVE
        assert repository.get(other_actor, workspace) is None
        assert repository.get(actor, other_workspace) is None
    finally:
        if storage is not None:
            storage.close()


def test_memberships_survive_close_and_reconstruction(tmp_path) -> None:
    path = tmp_path / "durable.sqlite3"
    actor = ActorIdentity("actor")
    active_workspace = WorkspaceIdentity("active")
    inactive_workspace = WorkspaceIdentity("inactive")
    with SQLiteLocalStorage(path) as first:
        first.initialize()
        first.create(actor, active_workspace)
        first.create(actor, inactive_workspace)
        first.deactivate(actor, inactive_workspace)
    with SQLiteLocalStorage(path) as second:
        second.initialize()
        assert second.get(actor, active_workspace).status is MembershipStatus.ACTIVE
        assert second.get(actor, inactive_workspace).status is MembershipStatus.INACTIVE
        assert second.get(actor, WorkspaceIdentity("missing")) is None


def test_membership_constraints_reject_duplicate_null_and_invalid_status(
    tmp_path,
) -> None:
    path = tmp_path / "constraints.sqlite3"
    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO actor_workspace_memberships "
            "VALUES ('actor', 'workspace', 'active')"
        )
        for values in (
            ("actor", "workspace", "inactive"),
            (None, "workspace", "active"),
            ("actor", None, "active"),
            ("actor", "other", None),
            ("actor", "other", "invalid"),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO actor_workspace_memberships VALUES (?, ?, ?)", values
                )


def test_v2_metadata_and_required_membership_schema_are_verified(tmp_path) -> None:
    metadata_path = tmp_path / "metadata.sqlite3"
    _create_v1_database(metadata_path)
    with sqlite3.connect(metadata_path) as connection:
        connection.execute("UPDATE schema_metadata SET schema_version = 1")
        connection.execute("PRAGMA user_version = 2")
    missing_path = tmp_path / "missing.sqlite3"
    _create_v1_database(missing_path)
    with sqlite3.connect(missing_path) as connection:
        connection.execute("UPDATE schema_metadata SET schema_version = 2")
        connection.execute("PRAGMA user_version = 2")
    for path in (metadata_path, missing_path):
        with SQLiteLocalStorage(path) as storage:
            with pytest.raises(LocalStorageError, match="schema is invalid"):
                storage.initialize()


def test_membership_errors_are_safe_and_invalid_persisted_status_fails(
    tmp_path,
) -> None:
    path = tmp_path / "errors.sqlite3"
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("workspace")
    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        storage._connection.execute("DROP TABLE actor_workspace_memberships")
        with pytest.raises(MembershipRepositoryError, match="Membership read failed"):
            storage.get(actor, workspace)
    corrupt_path = tmp_path / "corrupt.sqlite3"
    with SQLiteLocalStorage(corrupt_path) as storage:
        storage.initialize()
        storage._connection.execute("PRAGMA ignore_check_constraints = ON")
        storage._connection.execute(
            "INSERT INTO actor_workspace_memberships VALUES (?, ?, ?)",
            ("actor", "workspace", "corrupt"),
        )
        with pytest.raises(
            MembershipRepositoryError, match="Membership data is invalid"
        ):
            storage.get(actor, workspace)


@pytest.mark.parametrize("operation", ("get", "create", "activate", "deactivate"))
def test_membership_operations_require_exact_canonical_identities(
    operation, tmp_path
) -> None:
    with SQLiteLocalStorage(tmp_path / "types.sqlite3") as storage:
        storage.initialize()
        method = getattr(storage, operation)
        with pytest.raises(ValueError, match="actor is invalid"):
            method("actor", WorkspaceIdentity("workspace"))
        with pytest.raises(ValueError, match="workspace is invalid"):
            method(ActorIdentity("actor"), "workspace")
