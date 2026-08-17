"""SQLite adapters for explicitly composed local list and knowledge storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.cognition.local_resolution.contracts import (
    KnowledgeRecordConflict,
    LocalRepositoryError,
)
from app.cognition.local_resolution.models import (
    KNOWLEDGE_DISCOVERY_LOOKAHEAD,
    ActorIdentity,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRead,
    KnowledgeRecord,
    KnowledgeStored,
    ListItemsAdded,
    ListItemsSnapshot,
    WorkspaceIdentity,
)
from app.membership.contracts import MembershipRepositoryError
from app.membership.models import ActorWorkspaceMembership, MembershipStatus

SCHEMA_VERSION = 2


class LocalStorageError(LocalRepositoryError):
    """Safe storage lifecycle failure."""


class UnsupportedSchemaVersion(LocalStorageError):
    """The database belongs to a newer unsupported schema."""


class SQLiteLocalStorage:
    """One explicitly opened connection implementing both narrow repositories."""

    def __init__(self, database_path: str | Path) -> None:
        if isinstance(database_path, str) and (
            not database_path.strip() or database_path.endswith(("/", "\\"))
        ):
            raise ValueError("Database path must include a filename.")
        path = Path(database_path)
        if path.name in {"", ".", ".."}:
            raise ValueError("Database path must include a filename.")
        self._database_path = path
        self._connection: sqlite3.Connection | None = None

    @property
    def database_path(self) -> Path:
        return self._database_path

    @property
    def is_open(self) -> bool:
        return self._connection is not None

    def open(self) -> None:
        if self._connection is not None:
            return
        self._connection = sqlite3.connect(self._database_path)
        self._connection.execute("PRAGMA foreign_keys = ON")

    def initialize(self) -> None:
        connection = self._require_connection()
        current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if current_version > SCHEMA_VERSION:
            raise UnsupportedSchemaVersion("Local database schema is unsupported.")
        if current_version == SCHEMA_VERSION:
            self._verify_schema(connection, SCHEMA_VERSION, require_memberships=True)
            return
        if current_version == 1:
            self._migrate_v1_to_v2(connection)
            return
        if current_version != 0:
            raise LocalStorageError("Local database schema cannot be initialized.")
        with connection:
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
            self._create_membership_table(connection)
            connection.execute(
                "INSERT INTO schema_metadata (schema_key, schema_version) "
                "VALUES (?, ?)",
                ("local_storage", SCHEMA_VERSION),
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _migrate_v1_to_v2(self, connection: sqlite3.Connection) -> None:
        self._verify_schema(connection, 1, require_memberships=False)
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._create_membership_table(connection)
            connection.execute(
                "UPDATE schema_metadata SET schema_version = ? "
                "WHERE schema_key = ?",
                (SCHEMA_VERSION, "local_storage"),
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            connection.commit()
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise LocalStorageError("Local database migration failed.") from error

    @staticmethod
    def _create_membership_table(connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE actor_workspace_memberships ("
            "actor_id TEXT NOT NULL, workspace_id TEXT NOT NULL, "
            "status TEXT NOT NULL CHECK (status IN ('active', 'inactive')), "
            "PRIMARY KEY (actor_id, workspace_id))"
        )

    def close(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            connection.close()

    def __enter__(self) -> SQLiteLocalStorage:
        self.open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def add(
        self, workspace: WorkspaceIdentity, list_id: str, items: tuple[str, ...]
    ) -> ListItemsAdded:
        connection = self._require_initialized_connection()
        if not isinstance(workspace, WorkspaceIdentity) or not list_id.strip():
            raise ValueError("Valid workspace and list ID are required.")
        normalized_list_id = list_id.strip()
        normalized_items = tuple(item.strip() for item in items)
        if any(not item for item in normalized_items):
            raise ValueError("List item cannot be empty.")
        added: list[str] = []
        duplicates: list[str] = []
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT COALESCE(MAX(position), -1) FROM list_items "
                "WHERE workspace_id = ? AND list_id = ?",
                (workspace.workspace_id, normalized_list_id),
            ).fetchone()
            next_position = int(row[0]) + 1
            accepted = {
                result[0]
                for result in connection.execute(
                    "SELECT normalized_item FROM list_items "
                    "WHERE workspace_id = ? AND list_id = ?",
                    (workspace.workspace_id, normalized_list_id),
                )
            }
            for display_item in normalized_items:
                comparison = display_item.casefold()
                if comparison in accepted:
                    duplicates.append(display_item)
                    continue
                connection.execute(
                    "INSERT INTO list_items "
                    "(workspace_id, list_id, normalized_item, display_item, position) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        workspace.workspace_id,
                        normalized_list_id,
                        comparison,
                        display_item,
                        next_position,
                    ),
                )
                accepted.add(comparison)
                added.append(display_item)
                next_position += 1
            connection.commit()
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise LocalStorageError("Local list write failed.") from error
        snapshot = self.read(workspace, normalized_list_id)
        return ListItemsAdded(tuple(added), tuple(duplicates), snapshot.items)

    def read(self, workspace: WorkspaceIdentity, identifier: str) -> ListItemsSnapshot:
        """Read a list by list ID; use read_knowledge for knowledge records."""
        connection = self._require_initialized_connection()
        if not isinstance(workspace, WorkspaceIdentity) or not identifier.strip():
            raise ValueError("Valid workspace and identifier are required.")
        try:
            rows = connection.execute(
                "SELECT display_item FROM list_items "
                "WHERE workspace_id = ? AND list_id = ? ORDER BY position",
                (workspace.workspace_id, identifier.strip()),
            ).fetchall()
        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local list read failed.") from error
        return ListItemsSnapshot(tuple(row[0] for row in rows))

    def store(self, record: KnowledgeRecord) -> KnowledgeStored:
        connection = self._require_initialized_connection()
        if not isinstance(record, KnowledgeRecord):
            raise ValueError("A valid knowledge record is required.")
        values = (
            record.workspace.workspace_id,
            record.record_id,
            record.kind.value,
            record.key,
            record.value,
            record.provenance.source_type,
            record.provenance.source_reference,
        )
        try:
            with connection:
                connection.execute(
                    "INSERT INTO knowledge_records "
                    "(workspace_id, record_id, kind, knowledge_key, knowledge_value, "
                    "source_type, source_reference) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    values,
                )
            return KnowledgeStored(record, True)
        except sqlite3.IntegrityError:
            existing = self.read_knowledge(record.workspace, record.record_id).record
            if existing == record:
                return KnowledgeStored(existing, False)
            raise KnowledgeRecordConflict("Knowledge record already exists.") from None
        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local knowledge write failed.") from error

    def read_knowledge(
        self, workspace: WorkspaceIdentity, record_id: str
    ) -> KnowledgeRead:
        connection = self._require_initialized_connection()
        if not isinstance(workspace, WorkspaceIdentity) or not record_id.strip():
            raise ValueError("Valid workspace and record ID are required.")
        try:
            row = connection.execute(
                "SELECT kind, knowledge_key, knowledge_value, source_type, "
                "source_reference FROM knowledge_records "
                "WHERE workspace_id = ? AND record_id = ?",
                (workspace.workspace_id, record_id.strip()),
            ).fetchone()
        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local knowledge read failed.") from error
        if row is None:
            return KnowledgeRead(None)
        return KnowledgeRead(
            KnowledgeRecord(
                record_id.strip(),
                workspace,
                KnowledgeKind(row[0]),
                row[1],
                row[2],
                KnowledgeProvenance(row[3], row[4]),
            )
        )

    def find_knowledge_by_key(
        self,
        workspace: WorkspaceIdentity,
        key: str,
        kind: KnowledgeKind | None = None,
    ) -> tuple[KnowledgeRecord, ...]:
        connection = self._require_initialized_connection()
        if (
            not isinstance(workspace, WorkspaceIdentity)
            or not isinstance(key, str)
            or not key.strip()
        ):
            raise ValueError("Valid workspace and knowledge key are required.")
        if kind is not None and not isinstance(kind, KnowledgeKind):
            raise ValueError("Knowledge kind is invalid.")
        select = (
            "SELECT record_id, kind, knowledge_key, knowledge_value, "
            "source_type, source_reference FROM knowledge_records "
            "WHERE workspace_id = ? AND knowledge_key = ? "
        )
        try:
            if kind is None:
                rows = connection.execute(
                    select + "ORDER BY record_id COLLATE BINARY ASC LIMIT ?",
                    (
                        workspace.workspace_id,
                        key.strip(),
                        KNOWLEDGE_DISCOVERY_LOOKAHEAD,
                    ),
                ).fetchall()
            else:
                rows = connection.execute(
                    select
                    + "AND kind = ? ORDER BY record_id COLLATE BINARY ASC LIMIT ?",
                    (
                        workspace.workspace_id,
                        key.strip(),
                        kind.value,
                        KNOWLEDGE_DISCOVERY_LOOKAHEAD,
                    ),
                ).fetchall()
        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local knowledge discovery failed.") from error
        return tuple(
            KnowledgeRecord(
                row[0],
                workspace,
                KnowledgeKind(row[1]),
                row[2],
                row[3],
                KnowledgeProvenance(row[4], row[5]),
            )
            for row in rows
        )

    def get(
        self, actor: ActorIdentity, workspace: WorkspaceIdentity
    ) -> ActorWorkspaceMembership | None:
        key = self._membership_key(actor, workspace)
        try:
            connection = self._require_initialized_connection()
            row = connection.execute(
                "SELECT actor_id, workspace_id, status "
                "FROM actor_workspace_memberships "
                "WHERE actor_id = ? AND workspace_id = ?",
                key,
            ).fetchone()
            return self._membership_from_row(row)
        except MembershipRepositoryError:
            raise
        except (sqlite3.DatabaseError, LocalStorageError) as error:
            raise MembershipRepositoryError("Membership read failed.") from error

    def create(
        self, actor: ActorIdentity, workspace: WorkspaceIdentity
    ) -> ActorWorkspaceMembership:
        key = self._membership_key(actor, workspace)
        try:
            connection = self._require_initialized_connection()
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT OR IGNORE INTO actor_workspace_memberships "
                "(actor_id, workspace_id, status) VALUES (?, ?, ?)",
                (*key, MembershipStatus.ACTIVE.value),
            )
            membership = self._read_membership(connection, key)
            if membership is None:
                raise MembershipRepositoryError("Membership write failed.")
            connection.commit()
            return membership
        except MembershipRepositoryError:
            self._rollback_membership_write()
            raise
        except (sqlite3.DatabaseError, LocalStorageError) as error:
            self._rollback_membership_write()
            raise MembershipRepositoryError("Membership write failed.") from error

    def activate(
        self, actor: ActorIdentity, workspace: WorkspaceIdentity
    ) -> ActorWorkspaceMembership | None:
        return self._set_membership_status(actor, workspace, MembershipStatus.ACTIVE)

    def deactivate(
        self, actor: ActorIdentity, workspace: WorkspaceIdentity
    ) -> ActorWorkspaceMembership | None:
        return self._set_membership_status(actor, workspace, MembershipStatus.INACTIVE)

    def _set_membership_status(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        status: MembershipStatus,
    ) -> ActorWorkspaceMembership | None:
        key = self._membership_key(actor, workspace)
        try:
            connection = self._require_initialized_connection()
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE actor_workspace_memberships SET status = ? "
                "WHERE actor_id = ? AND workspace_id = ?",
                (status.value, *key),
            )
            membership = self._read_membership(connection, key)
            connection.commit()
            return membership
        except MembershipRepositoryError:
            self._rollback_membership_write()
            raise
        except (sqlite3.DatabaseError, LocalStorageError) as error:
            self._rollback_membership_write()
            raise MembershipRepositoryError("Membership write failed.") from error

    def _rollback_membership_write(self) -> None:
        connection = self._connection
        if connection is not None and connection.in_transaction:
            connection.rollback()

    @staticmethod
    def _membership_key(
        actor: ActorIdentity, workspace: WorkspaceIdentity
    ) -> tuple[str, str]:
        if type(actor) is not ActorIdentity:
            raise ValueError("Membership actor is invalid.")
        if type(workspace) is not WorkspaceIdentity:
            raise ValueError("Membership workspace is invalid.")
        return actor.actor_id, workspace.workspace_id

    @classmethod
    def _read_membership(
        cls,
        connection: sqlite3.Connection,
        key: tuple[str, str],
    ) -> ActorWorkspaceMembership | None:
        row = connection.execute(
            "SELECT actor_id, workspace_id, status "
            "FROM actor_workspace_memberships "
            "WHERE actor_id = ? AND workspace_id = ?",
            key,
        ).fetchone()
        return cls._membership_from_row(row)

    @staticmethod
    def _membership_from_row(
        row: tuple[str, str, str] | None,
    ) -> ActorWorkspaceMembership | None:
        if row is None:
            return None
        try:
            status = MembershipStatus(row[2])
            return ActorWorkspaceMembership(
                ActorIdentity(row[0]), WorkspaceIdentity(row[1]), status
            )
        except ValueError as error:
            raise MembershipRepositoryError("Membership data is invalid.") from error

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise LocalStorageError("Local storage is not open.")
        return self._connection

    def _require_initialized_connection(self) -> sqlite3.Connection:
        connection = self._require_connection()
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version != SCHEMA_VERSION:
            raise LocalStorageError("Local storage is not initialized.")
        return connection

    @staticmethod
    def _verify_schema(
        connection: sqlite3.Connection,
        expected_version: int,
        *,
        require_memberships: bool,
    ) -> None:
        try:
            row = connection.execute(
                "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
                ("local_storage",),
            ).fetchone()
            actual_columns: tuple[tuple[object, ...], ...] = ()
            if require_memberships:
                columns = connection.execute(
                    "PRAGMA table_info(actor_workspace_memberships)"
                ).fetchall()
                table_row = connection.execute(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = ?",
                    ("actor_workspace_memberships",),
                ).fetchone()
                actual_columns = tuple(
                    (column[1], column[2], column[3], column[5])
                    for column in columns
                )
        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local database schema is invalid.") from error
        if row is None or int(row[0]) != expected_version:
            raise LocalStorageError("Local database schema is invalid.")
        expected_columns = (
            ("actor_id", "TEXT", 1, 1),
            ("workspace_id", "TEXT", 1, 2),
            ("status", "TEXT", 1, 0),
        )
        if require_memberships and actual_columns != expected_columns:
            raise LocalStorageError("Local database schema is invalid.")
        if require_memberships and (
            table_row is None
            or "status IN ('active', 'inactive')" not in str(table_row[0])
        ):
            raise LocalStorageError("Local database schema is invalid.")


class SQLiteKnowledgeRecordRepository:
    """Narrow knowledge view over an explicitly owned SQLite storage."""

    def __init__(self, storage: SQLiteLocalStorage) -> None:
        self._storage = storage

    def store(self, record: KnowledgeRecord) -> KnowledgeStored:
        return self._storage.store(record)

    def read(self, workspace: WorkspaceIdentity, record_id: str) -> KnowledgeRead:
        return self._storage.read_knowledge(workspace, record_id)

    def find_by_key(
        self,
        workspace: WorkspaceIdentity,
        key: str,
        kind: KnowledgeKind | None = None,
    ) -> tuple[KnowledgeRecord, ...]:
        return self._storage.find_knowledge_by_key(workspace, key, kind)
