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
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRead,
    KnowledgeRecord,
    KnowledgeStored,
    ListItemsAdded,
    ListItemsSnapshot,
    WorkspaceIdentity,
)

SCHEMA_VERSION = 1


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
            self._verify_schema_metadata(connection)
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
            connection.execute(
                "INSERT INTO schema_metadata (schema_key, schema_version) "
                "VALUES (?, ?)",
                ("local_storage", SCHEMA_VERSION),
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

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
    def _verify_schema_metadata(connection: sqlite3.Connection) -> None:
        try:
            row = connection.execute(
                "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
                ("local_storage",),
            ).fetchone()
        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local database schema is invalid.") from error
        if row is None or int(row[0]) != SCHEMA_VERSION:
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
