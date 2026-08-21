"""SQLite adapters for explicitly composed local list and knowledge storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.cognition.local_resolution.contracts import (
    KnowledgeRecordConflict,
    LocalRepositoryError,
    PermissionGrantConflict,
    PermissionGrantRepositoryError,
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
from app.principal_authentication.contracts import (
    PrincipalActorMappingConflict,
    PrincipalActorMappingRepositoryError,
)
from app.principal_authentication.models import PrincipalIdentity

SCHEMA_VERSION = 4


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
            self._verify_schema(
                connection,
                SCHEMA_VERSION,
                require_memberships=True,
                require_principal_mappings=True,
                require_permission_grants=True,
            )
            return
        if current_version == 3:
            self._migrate_v3_to_v4(connection)
            return
        if current_version == 2:
            self._migrate_v2_to_v3(connection)
            self._migrate_v3_to_v4(connection)
            return
        if current_version == 1:
            self._migrate_v1_to_v2(connection)
            self._migrate_v2_to_v3(connection)
            self._migrate_v3_to_v4(connection)
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
            self._create_principal_actor_mapping_table(connection)
            self._create_action_permission_grant_table(connection)
            connection.execute(
                "INSERT INTO schema_metadata (schema_key, schema_version) "
                "VALUES (?, ?)",
                ("local_storage", SCHEMA_VERSION),
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _migrate_v1_to_v2(self, connection: sqlite3.Connection) -> None:
        self._verify_schema(
            connection,
            1,
            require_memberships=False,
            require_principal_mappings=False,
        )
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._create_membership_table(connection)
            connection.execute(
                "UPDATE schema_metadata SET schema_version = ? "
                "WHERE schema_key = ?",
                (2, "local_storage"),
            )
            connection.execute("PRAGMA user_version = 2")
            connection.commit()
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise LocalStorageError("Local database migration failed.") from error

    def _migrate_v2_to_v3(self, connection: sqlite3.Connection) -> None:
        self._verify_schema(
            connection,
            2,
            require_memberships=True,
            require_principal_mappings=False,
        )
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._create_principal_actor_mapping_table(connection)
            connection.execute(
                "UPDATE schema_metadata SET schema_version = ? "
                "WHERE schema_key = ?",
                (3, "local_storage"),
            )
            connection.execute("PRAGMA user_version = 3")
            connection.commit()
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise LocalStorageError("Local database migration failed.") from error

    def _migrate_v3_to_v4(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        self._verify_schema(
            connection,
            3,
            require_memberships=True,
            require_principal_mappings=True,
            require_permission_grants=False,
        )
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._create_action_permission_grant_table(
                connection
            )
            connection.execute(
                "UPDATE schema_metadata SET schema_version = ? "
                "WHERE schema_key = ?",
                (SCHEMA_VERSION, "local_storage"),
            )
            connection.execute(
                f"PRAGMA user_version = {SCHEMA_VERSION}"
            )
            connection.commit()
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise LocalStorageError(
                "Local database migration failed."
            ) from error

    @staticmethod
    def _create_membership_table(connection: sqlite3.Connection) -> None:
        connection.execute(
            "CREATE TABLE actor_workspace_memberships ("
            "actor_id TEXT NOT NULL, workspace_id TEXT NOT NULL, "
            "status TEXT NOT NULL CHECK (status IN ('active', 'inactive')), "
            "PRIMARY KEY (actor_id, workspace_id))"
        )

    @staticmethod
    def _create_principal_actor_mapping_table(
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            "CREATE TABLE principal_actor_mappings ("
            "principal_id TEXT NOT NULL COLLATE BINARY PRIMARY KEY, "
            "actor_id TEXT NOT NULL)"
        )

    @staticmethod
    def _create_action_permission_grant_table(
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            "CREATE TABLE action_permission_grants ("
            "actor_id TEXT NOT NULL COLLATE BINARY, "
            "workspace_id TEXT NOT NULL COLLATE BINARY, "
            "action TEXT NOT NULL COLLATE BINARY, "
            "PRIMARY KEY "
            "(actor_id, workspace_id, action))"
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

    def read_principal_actor_mapping(
        self,
        principal: PrincipalIdentity,
    ) -> ActorIdentity | None:
        if type(principal) is not PrincipalIdentity:
            raise ValueError("Principal identity is invalid.")
        try:
            connection = self._require_initialized_connection()
            row = connection.execute(
                "SELECT actor_id FROM principal_actor_mappings "
                "WHERE principal_id = ?",
                (principal.principal_id,),
            ).fetchone()
            if row is None:
                return None
            try:
                return ActorIdentity(row[0])
            except ValueError as error:
                raise PrincipalActorMappingRepositoryError(
                    "Principal actor mapping data is invalid."
                ) from error
        except PrincipalActorMappingRepositoryError:
            raise
        except (sqlite3.DatabaseError, LocalStorageError) as error:
            raise PrincipalActorMappingRepositoryError(
                "Principal actor mapping read failed."
            ) from error

    def create_principal_actor_mapping(
        self,
        principal: PrincipalIdentity,
        actor: ActorIdentity,
    ) -> ActorIdentity:
        if type(principal) is not PrincipalIdentity:
            raise ValueError("Principal identity is invalid.")
        if type(actor) is not ActorIdentity:
            raise ValueError("Actor identity is invalid.")
        try:
            connection = self._require_initialized_connection()
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO principal_actor_mappings "
                "(principal_id, actor_id) VALUES (?, ?)",
                (principal.principal_id, actor.actor_id),
            )
            connection.commit()
            return actor
        except sqlite3.IntegrityError:
            self._rollback_principal_actor_mapping_write()
            raise PrincipalActorMappingConflict(
                "Principal actor mapping already exists."
            ) from None
        except (sqlite3.DatabaseError, LocalStorageError) as error:
            self._rollback_principal_actor_mapping_write()
            raise PrincipalActorMappingRepositoryError(
                "Principal actor mapping write failed."
            ) from error

    def _rollback_principal_actor_mapping_write(self) -> None:
        connection = self._connection
        if connection is not None and connection.in_transaction:
            connection.rollback()

    def is_permission_granted(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool:
        key = self._permission_key(
            actor,
            workspace,
            action,
        )

        try:
            connection = (
                self._require_initialized_connection()
            )

            row = connection.execute(
                "SELECT 1 "
                "FROM action_permission_grants "
                "WHERE actor_id = ? "
                "AND workspace_id = ? "
                "AND action = ? "
                "LIMIT 1",
                key,
            ).fetchone()

            return row is not None

        except PermissionGrantRepositoryError:
            raise

        except (
            sqlite3.DatabaseError,
            LocalStorageError,
        ) as error:
            raise PermissionGrantRepositoryError(
                "Permission grant read failed."
            ) from error

    def create_permission_grant(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> None:
        key = self._permission_key(
            actor,
            workspace,
            action,
        )

        try:
            connection = (
                self._require_initialized_connection()
            )

            connection.execute(
                "BEGIN IMMEDIATE"
            )

            connection.execute(
                "INSERT INTO action_permission_grants "
                "(actor_id, workspace_id, action) "
                "VALUES (?, ?, ?)",
                key,
            )

            connection.commit()

        except sqlite3.IntegrityError as error:
            self._rollback_permission_grant_write()

            if (
                getattr(
                    error,
                    "sqlite_errorcode",
                    None,
                )
                == sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY
            ):
                raise PermissionGrantConflict(
                    "Permission grant already exists."
                ) from None

            raise PermissionGrantRepositoryError(
                "Permission grant write failed."
            ) from error

        except PermissionGrantRepositoryError:
            self._rollback_permission_grant_write()
            raise

        except (
            sqlite3.DatabaseError,
            LocalStorageError,
        ) as error:
            self._rollback_permission_grant_write()

            raise PermissionGrantRepositoryError(
                "Permission grant write failed."
            ) from error

    def _rollback_permission_grant_write(self) -> None:
        connection = self._connection

        if (
            connection is not None
            and connection.in_transaction
        ):
            connection.rollback()

    @staticmethod
    def _permission_key(
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> tuple[str, str, str]:
        if type(actor) is not ActorIdentity:
            raise ValueError(
                "Permission actor is invalid."
            )

        if type(workspace) is not WorkspaceIdentity:
            raise ValueError(
                "Permission workspace is invalid."
            )

        if (
            type(action) is not str
            or not action.strip()
        ):
            raise ValueError(
                "Permission action is invalid."
            )

        return (
            actor.actor_id,
            workspace.workspace_id,
            action,
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
    def _verify_schema(
        connection: sqlite3.Connection,
        expected_version: int,
        *,
        require_memberships: bool,
        require_principal_mappings: bool,
        require_permission_grants: bool = False,
    ) -> None:
        membership_columns: tuple[tuple[object, ...], ...] = ()
        membership_table_row: tuple[object, ...] | None = None
        mapping_columns: tuple[tuple[object, ...], ...] = ()
        mapping_table_row: tuple[object, ...] | None = None
        mapping_has_unapproved_unique_index = False
        permission_columns: tuple[tuple[object, ...], ...] = ()
        permission_table_row: tuple[object, ...] | None = None
        permission_has_unapproved_unique_index = False

        try:
            row = connection.execute(
                "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
                ("local_storage",),
            ).fetchone()

            if require_memberships:
                columns = connection.execute(
                    "PRAGMA table_info(actor_workspace_memberships)"
                ).fetchall()
                membership_table_row = connection.execute(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = ?",
                    ("actor_workspace_memberships",),
                ).fetchone()
                membership_columns = tuple(
                    (column[1], column[2], column[3], column[5])
                    for column in columns
                )

            if require_principal_mappings:
                columns = connection.execute(
                    "PRAGMA table_info(principal_actor_mappings)"
                ).fetchall()
                mapping_table_row = connection.execute(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = ?",
                    ("principal_actor_mappings",),
                ).fetchone()
                mapping_columns = tuple(
                    (column[1], column[2], column[3], column[5])
                    for column in columns
                )

                mapping_indexes = connection.execute(
                    "PRAGMA index_list(principal_actor_mappings)"
                ).fetchall()

                for index in mapping_indexes:
                    if not bool(index[2]):
                        continue

                    index_name = str(index[1]).replace(
                        '"',
                        '""',
                    )
                    index_origin = (
                        str(index[3])
                        if len(index) > 3
                        else ""
                    )

                    index_columns = tuple(
                        row[2]
                        for row in connection.execute(
                            f'PRAGMA index_info("{index_name}")'
                        ).fetchall()
                    )

                    if (
                        index_origin == "pk"
                        and index_columns == ("principal_id",)
                    ):
                        continue

                    mapping_has_unapproved_unique_index = True
                    break

            if require_permission_grants:
                columns = connection.execute(
                    "PRAGMA table_info("
                    "action_permission_grants)"
                ).fetchall()

                permission_table_row = connection.execute(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = ?",
                    ("action_permission_grants",),
                ).fetchone()

                permission_columns = tuple(
                    (
                        column[1],
                        column[2],
                        column[3],
                        column[5],
                    )
                    for column in columns
                )

                permission_indexes = connection.execute(
                    "PRAGMA index_list("
                    "action_permission_grants)"
                ).fetchall()

                for index in permission_indexes:
                    if not bool(index[2]):
                        continue

                    index_name = str(index[1]).replace(
                        '"',
                        '""',
                    )

                    index_origin = (
                        str(index[3])
                        if len(index) > 3
                        else ""
                    )

                    index_columns = tuple(
                        item[2]
                        for item in connection.execute(
                            f'PRAGMA index_info('
                            f'"{index_name}")'
                        ).fetchall()
                    )

                    if (
                        index_origin == "pk"
                        and index_columns
                        == (
                            "actor_id",
                            "workspace_id",
                            "action",
                        )
                    ):
                        continue

                    permission_has_unapproved_unique_index = (
                        True
                    )
                    break

        except sqlite3.DatabaseError as error:
            raise LocalStorageError("Local database schema is invalid.") from error

        if row is None or int(row[0]) != expected_version:
            raise LocalStorageError("Local database schema is invalid.")

        expected_membership_columns = (
            ("actor_id", "TEXT", 1, 1),
            ("workspace_id", "TEXT", 1, 2),
            ("status", "TEXT", 1, 0),
        )
        if require_memberships and membership_columns != expected_membership_columns:
            raise LocalStorageError("Local database schema is invalid.")
        if require_memberships and (
            membership_table_row is None
            or "status IN ('active', 'inactive')"
            not in str(membership_table_row[0])
        ):
            raise LocalStorageError("Local database schema is invalid.")

        expected_mapping_columns = (
            ("principal_id", "TEXT", 1, 1),
            ("actor_id", "TEXT", 1, 0),
        )
        if (
            require_principal_mappings
            and mapping_columns != expected_mapping_columns
        ):
            raise LocalStorageError("Local database schema is invalid.")
        if require_principal_mappings:
            if mapping_table_row is None:
                raise LocalStorageError("Local database schema is invalid.")
            mapping_sql = " ".join(str(mapping_table_row[0]).split()).lower()
            if (
                "principal_id text not null collate binary primary key"
                not in mapping_sql
                or "actor_id text not null" not in mapping_sql
                or "unique (actor_id)" in mapping_sql
                or mapping_has_unapproved_unique_index
            ):
                raise LocalStorageError(
                    "Local database schema is invalid."
                )

        expected_permission_columns = (
            ("actor_id", "TEXT", 1, 1),
            ("workspace_id", "TEXT", 1, 2),
            ("action", "TEXT", 1, 3),
        )

        if (
            require_permission_grants
            and permission_columns
            != expected_permission_columns
        ):
            raise LocalStorageError(
                "Local database schema is invalid."
            )

        if require_permission_grants:
            if permission_table_row is None:
                raise LocalStorageError(
                    "Local database schema is invalid."
                )

            permission_sql = " ".join(
                str(permission_table_row[0]).split()
            ).lower()

            expected_permission_sql = (
                "create table action_permission_grants "
                "(actor_id text not null collate binary, "
                "workspace_id text not null collate binary, "
                "action text not null collate binary, "
                "primary key "
                "(actor_id, workspace_id, action))"
            )

            if (
                permission_sql != expected_permission_sql
                or permission_has_unapproved_unique_index
            ):
                raise LocalStorageError(
                    "Local database schema is invalid."
                )


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


class SQLitePrincipalActorMappingRepository:
    """Narrow principal-to-actor view over explicitly owned SQLite storage."""

    def __init__(self, storage: SQLiteLocalStorage) -> None:
        self._storage = storage

    def get(self, principal: PrincipalIdentity) -> ActorIdentity | None:
        return self._storage.read_principal_actor_mapping(principal)

    def create(
        self,
        principal: PrincipalIdentity,
        actor: ActorIdentity,
    ) -> ActorIdentity:
        return self._storage.create_principal_actor_mapping(principal, actor)


class SQLitePermissionGrantRepository:
    """Narrow action-permission view over explicitly owned SQLite storage."""

    __slots__ = ("_storage",)

    def __init__(
        self,
        storage: SQLiteLocalStorage,
    ) -> None:
        if storage is None:
            raise ValueError(
                "A local storage instance is required."
            )

        self._storage = storage

    def is_granted(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool:
        return self._storage.is_permission_granted(
            actor,
            workspace,
            action,
        )

    def create(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> None:
        self._storage.create_permission_grant(
            actor,
            workspace,
            action,
        )
