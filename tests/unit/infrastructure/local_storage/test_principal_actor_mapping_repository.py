"""Durable principal-to-actor mapping storage behavior."""

import sqlite3
from pathlib import Path

import pytest

from app.cognition.local_resolution.models import (
    ActorIdentity,
    WorkspaceIdentity,
)
from app.infrastructure.local_storage.sqlite_storage import (
    SCHEMA_VERSION,
    LocalStorageError,
    SQLiteLocalStorage,
    SQLitePrincipalActorMappingRepository,
)
from app.membership import MembershipStatus
from app.principal_authentication.contracts import (
    PrincipalActorMappingConflict,
    PrincipalActorMappingRepositoryError,
)
from app.principal_authentication.models import (
    PrincipalActorMappingErrorCode,
    PrincipalIdentity,
)
from app.principal_authentication.repository_mapper import (
    RepositoryPrincipalActorMapper,
)


def _create_v2_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE schema_metadata ("
            "schema_key TEXT PRIMARY KEY, "
            "schema_version INTEGER NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE list_items ("
            "workspace_id TEXT NOT NULL, "
            "list_id TEXT NOT NULL, "
            "normalized_item TEXT NOT NULL, "
            "display_item TEXT NOT NULL, "
            "position INTEGER NOT NULL, "
            "PRIMARY KEY "
            "(workspace_id, list_id, normalized_item), "
            "UNIQUE (workspace_id, list_id, position))"
        )
        connection.execute(
            "CREATE TABLE knowledge_records ("
            "workspace_id TEXT NOT NULL, "
            "record_id TEXT NOT NULL, "
            "kind TEXT NOT NULL, "
            "knowledge_key TEXT NOT NULL, "
            "knowledge_value TEXT NOT NULL, "
            "source_type TEXT NOT NULL, "
            "source_reference TEXT NOT NULL, "
            "PRIMARY KEY (workspace_id, record_id))"
        )
        connection.execute(
            "CREATE TABLE actor_workspace_memberships ("
            "actor_id TEXT NOT NULL, "
            "workspace_id TEXT NOT NULL, "
            "status TEXT NOT NULL "
            "CHECK (status IN ('active', 'inactive')), "
            "PRIMARY KEY (actor_id, workspace_id))"
        )
        connection.execute(
            "INSERT INTO schema_metadata "
            "VALUES ('local_storage', 2)"
        )
        connection.execute("PRAGMA user_version = 2")


def test_v2_to_v3_migration_preserves_existing_data(
    tmp_path,
) -> None:
    path = tmp_path / "migration.sqlite3"
    _create_v2_database(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO list_items VALUES (?, ?, ?, ?, ?)",
            ("home", "shopping", "milk", "Milk", 0),
        )
        connection.execute(
            "INSERT INTO knowledge_records "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "home",
                "record",
                "fact",
                "family.value",
                "exact",
                "reviewed",
                "source",
            ),
        )
        connection.execute(
            "INSERT INTO actor_workspace_memberships "
            "VALUES (?, ?, ?)",
            ("actor", "home", "inactive"),
        )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        workspace = WorkspaceIdentity("home")
        actor = ActorIdentity("actor")

        assert storage.read(
            workspace,
            "shopping",
        ).items == ("Milk",)

        assert (
            storage.read_knowledge(
                workspace,
                "record",
            ).record.value
            == "exact"
        )

        assert (
            storage.get(actor, workspace).status
            is MembershipStatus.INACTIVE
        )

        repository = SQLitePrincipalActorMappingRepository(
            storage
        )

        assert repository.get(
            PrincipalIdentity("principal")
        ) is None

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "PRAGMA user_version"
        ).fetchone() == (SCHEMA_VERSION,)

        assert connection.execute(
            "SELECT schema_version "
            "FROM schema_metadata "
            "WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (SCHEMA_VERSION,)

        assert connection.execute(
            "SELECT count(*) FROM sqlite_master "
            "WHERE type = 'table' AND name = ?",
            ("principal_actor_mappings",),
        ).fetchone() == (1,)


def test_v2_to_v3_failure_rolls_back(
    tmp_path,
) -> None:
    path = tmp_path / "migration-failure.sqlite3"
    _create_v2_database(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO actor_workspace_memberships "
            "VALUES (?, ?, ?)",
            ("actor", "home", "active"),
        )
        connection.execute(
            "CREATE TRIGGER fail_schema_metadata_update "
            "BEFORE UPDATE ON schema_metadata BEGIN "
            "SELECT RAISE("
            "ABORT, 'forced migration failure'"
            "); END"
        )

    with SQLiteLocalStorage(path) as storage:
        with pytest.raises(
            LocalStorageError,
            match="migration failed",
        ):
            storage.initialize()

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "PRAGMA user_version"
        ).fetchone() == (2,)

        assert connection.execute(
            "SELECT schema_version "
            "FROM schema_metadata "
            "WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (2,)

        assert connection.execute(
            "SELECT count(*) FROM sqlite_master "
            "WHERE type = 'table' AND name = ?",
            ("principal_actor_mappings",),
        ).fetchone() == (0,)

        assert connection.execute(
            "SELECT actor_id, workspace_id, status "
            "FROM actor_workspace_memberships"
        ).fetchone() == (
            "actor",
            "home",
            "active",
        )

        connection.execute(
            "DROP TRIGGER fail_schema_metadata_update"
        )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "PRAGMA user_version"
        ).fetchone() == (SCHEMA_VERSION,)


def test_mapping_is_durable_exact_and_case_sensitive(
    tmp_path,
) -> None:
    path = tmp_path / "mapping.sqlite3"
    principal = PrincipalIdentity("Principal")
    actor = ActorIdentity("Actor")

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        repository = SQLitePrincipalActorMappingRepository(
            storage
        )

        assert repository.create(principal, actor) is actor
        assert repository.get(principal) == actor

        assert repository.get(
            PrincipalIdentity("principal")
        ) is None

        with pytest.raises(
            PrincipalActorMappingConflict
        ):
            repository.create(principal, actor)

        with pytest.raises(
            PrincipalActorMappingConflict
        ):
            repository.create(
                principal,
                ActorIdentity("other"),
            )

        repository.create(
            PrincipalIdentity("second"),
            actor,
        )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        repository = SQLitePrincipalActorMappingRepository(
            storage
        )

        assert repository.get(principal) == actor
        assert repository.get(
            PrincipalIdentity("second")
        ) == actor

        assert repository.get(
            PrincipalIdentity("principal")
        ) is None


def test_mapping_repository_requires_exact_identities(
    tmp_path,
) -> None:
    with SQLiteLocalStorage(
        tmp_path / "types.sqlite3"
    ) as storage:
        storage.initialize()

        repository = SQLitePrincipalActorMappingRepository(
            storage
        )

        with pytest.raises(
            ValueError,
            match="Principal identity",
        ):
            repository.get(object())

        with pytest.raises(
            ValueError,
            match="Principal identity",
        ):
            repository.create(
                object(),
                ActorIdentity("actor"),
            )

        with pytest.raises(
            ValueError,
            match="Actor identity",
        ):
            repository.create(
                PrincipalIdentity("principal"),
                object(),
            )


def test_mapping_repository_errors_fail_closed(
    tmp_path,
) -> None:
    path = tmp_path / "errors.sqlite3"

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        repository = SQLitePrincipalActorMappingRepository(
            storage
        )

        storage._connection.execute(
            "DROP TABLE principal_actor_mappings"
        )

        with pytest.raises(
            PrincipalActorMappingRepositoryError,
            match="mapping read failed",
        ):
            repository.get(
                PrincipalIdentity("principal")
            )

    corrupt = tmp_path / "corrupt.sqlite3"

    with SQLiteLocalStorage(corrupt) as storage:
        storage.initialize()

        storage._connection.execute(
            "INSERT INTO principal_actor_mappings "
            "(principal_id, actor_id) "
            "VALUES (?, ?)",
            ("principal", ""),
        )

        repository = SQLitePrincipalActorMappingRepository(
            storage
        )

        with pytest.raises(
            PrincipalActorMappingRepositoryError,
            match="mapping data is invalid",
        ):
            repository.get(
                PrincipalIdentity("principal")
            )


def test_repository_mapper_uses_sqlite_repository(
    tmp_path,
) -> None:
    path = tmp_path / "mapper.sqlite3"
    principal = PrincipalIdentity("Principal")
    actor = ActorIdentity("actor")

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        repository = SQLitePrincipalActorMappingRepository(
            storage
        )
        repository.create(principal, actor)

        mapper = RepositoryPrincipalActorMapper(
            repository
        )

        success = mapper.map(principal)

        assert success.success
        assert success.actor == actor
        assert success.error_code is None

        missing = mapper.map(
            PrincipalIdentity("principal")
        )

        assert not missing.success
        assert (
            missing.error_code
            is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED
        )

        storage._connection.execute(
            "DROP TABLE principal_actor_mappings"
        )

        failure = mapper.map(principal)

        assert not failure.success
        assert (
            failure.error_code
            is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
        )


def test_v3_verification_requires_mapping_table(
    tmp_path,
) -> None:
    path = tmp_path / "invalid-v3.sqlite3"
    _create_v2_database(path)

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE schema_metadata "
            "SET schema_version = ?",
            (SCHEMA_VERSION,),
        )
        connection.execute(
            f"PRAGMA user_version = {SCHEMA_VERSION}"
        )

    with SQLiteLocalStorage(path) as storage:
        with pytest.raises(
            LocalStorageError,
            match="schema is invalid",
        ):
            storage.initialize()


def test_v3_verification_rejects_unique_actor_index(
    tmp_path,
) -> None:
    path = tmp_path / "unique-actor-v3.sqlite3"

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE UNIQUE INDEX forbidden_unique_actor "
            "ON principal_actor_mappings(actor_id)"
        )

    with SQLiteLocalStorage(path) as storage:
        with pytest.raises(
            LocalStorageError,
            match="schema is invalid",
        ):
            storage.initialize()


def test_v3_verification_rejects_unique_actor_expression_index(
    tmp_path,
) -> None:
    path = tmp_path / "unique-actor-expression-v3.sqlite3"

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE UNIQUE INDEX "
            "forbidden_unique_actor_expression "
            "ON principal_actor_mappings(lower(actor_id))"
        )

    with SQLiteLocalStorage(path) as storage:
        with pytest.raises(
            LocalStorageError,
            match="schema is invalid",
        ):
            storage.initialize()
