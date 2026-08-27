"""Explicit local-development ownership for the interactive Luxiom runtime."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from secrets import token_urlsafe
from threading import Condition, RLock
from typing import Final

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
)
from app.core.config import Settings
from app.core.container import Container
from app.infrastructure.local_storage.sqlite_storage import (
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
    SQLitePrincipalActorMappingRepository,
)
from app.local_command import LocalCommandApplicationGateway
from app.membership.models import MembershipStatus
from app.principal_authentication import (
    ConfiguredPrincipalProofBinding,
    PrincipalIdentity,
)

DEVELOPMENT_PRINCIPAL: Final = PrincipalIdentity("luxiom-local-dev-principal")
DEVELOPMENT_ACTOR: Final = ActorIdentity("luxiom-local-dev-actor")
DEVELOPMENT_WORKSPACE: Final = WorkspaceIdentity("luxiom-local-dev-workspace")
DEVELOPMENT_PERMISSIONS: Final = (
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
)


class LocalInteractiveRuntimeState(str, Enum):
    """Closed lifecycle states for one non-restartable runtime instance."""

    NEW = "new"
    STARTED = "started"
    CLOSED = "closed"


class LocalInteractiveRuntimeError(RuntimeError):
    """Signal a safe local interactive runtime lifecycle failure."""


class LocalInteractiveRuntime:
    """Own one explicit SQLite-backed local-development composition."""

    __slots__ = (
        "_container",
        "_close_requested",
        "_csrf_token",
        "_database_path",
        "_development_proof",
        "_gateway",
        "_lifecycle_lock",
        "_lifecycle_condition",
        "_starting",
        "_state",
        "_storage",
    )

    def __init__(
        self,
        database_path: str | Path,
        development_proof: str,
    ) -> None:
        path = self._validate_database_path(database_path)
        if not isinstance(development_proof, str) or not development_proof.strip():
            raise ValueError("A non-empty development proof is required.")

        self._database_path = path
        self._development_proof: str | None = development_proof
        self._lifecycle_lock = RLock()
        self._lifecycle_condition = Condition(self._lifecycle_lock)
        self._state = LocalInteractiveRuntimeState.NEW
        self._starting = False
        self._close_requested = False
        self._storage: SQLiteLocalStorage | None = None
        self._container: Container | None = None
        self._gateway: LocalCommandApplicationGateway | None = None
        self._csrf_token: str | None = None

    @staticmethod
    def _validate_database_path(database_path: str | Path) -> Path:
        if isinstance(database_path, str) and (
            not database_path.strip() or database_path.endswith(("/", "\\"))
        ):
            raise ValueError("Database path must include a filename.")
        if not isinstance(database_path, (str, Path)):
            raise ValueError("Database path must include a filename.")
        path = Path(database_path)
        if path.name in {"", ".", ".."}:
            raise ValueError("Database path must include a filename.")
        return path

    @property
    def database_path(self) -> Path:
        return self._database_path

    @property
    def state(self) -> LocalInteractiveRuntimeState:
        return self._state

    @property
    def gateway(self) -> LocalCommandApplicationGateway:
        gateway = self._gateway
        if self._state is not LocalInteractiveRuntimeState.STARTED or gateway is None:
            raise LocalInteractiveRuntimeError("The runtime gateway is unavailable.")
        return gateway

    @property
    def csrf_token(self) -> str:
        csrf_token = self._csrf_token
        if (
            self._state is not LocalInteractiveRuntimeState.STARTED
            or csrf_token is None
        ):
            raise LocalInteractiveRuntimeError("The runtime CSRF token is unavailable.")
        return csrf_token

    def start(self) -> None:
        with self._lifecycle_condition:
            if self._state is not LocalInteractiveRuntimeState.NEW or self._starting:
                raise LocalInteractiveRuntimeError("The runtime cannot start.")
            self._starting = True
            self._close_requested = False
            proof = self._development_proof

        storage: SQLiteLocalStorage | None = None
        try:
            if proof is None:
                raise LocalInteractiveRuntimeError("The runtime cannot start.")

            storage = SQLiteLocalStorage(self._database_path)
            storage.open()
            storage.initialize()

            knowledge_repository = SQLiteKnowledgeRecordRepository(storage)
            mapping_repository = SQLitePrincipalActorMappingRepository(storage)
            permission_repository = SQLitePermissionGrantRepository(storage)

            self._bootstrap_mapping(mapping_repository)
            self._bootstrap_membership(storage)
            self._bootstrap_permissions(permission_repository)
            self._verify_bootstrap(
                storage,
                mapping_repository,
                permission_repository,
            )

            runtime_container = Container(
                Settings(REASONING_ENABLED=False, _env_file=None),
                local_permission_grant_repository=permission_repository,
                local_list_repository=storage,
                local_knowledge_repository=knowledge_repository,
                membership_repository=storage,
                principal_proof_bindings=(
                    ConfiguredPrincipalProofBinding(
                        DEVELOPMENT_PRINCIPAL,
                        proof,
                    ),
                ),
                principal_actor_mapping_repository=mapping_repository,
            )
            gateway = runtime_container.local_command_application_gateway
            if type(gateway) is not LocalCommandApplicationGateway:
                raise LocalInteractiveRuntimeError("The runtime cannot start.")
            csrf_token = token_urlsafe(32)
            if not csrf_token:
                raise LocalInteractiveRuntimeError("The runtime cannot start.")

            with self._lifecycle_condition:
                if self._close_requested:
                    raise LocalInteractiveRuntimeError("The runtime cannot start.")
                self._storage = storage
                self._container = runtime_container
                self._gateway = gateway
                self._csrf_token = csrf_token
                self._development_proof = None
                self._state = LocalInteractiveRuntimeState.STARTED
                self._starting = False
                self._lifecycle_condition.notify_all()
        except BaseException as error:
            if storage is not None:
                try:
                    storage.close()
                except BaseException:
                    pass
            with self._lifecycle_condition:
                self._storage = None
                self._container = None
                self._gateway = None
                self._csrf_token = None
                self._development_proof = None
                self._state = LocalInteractiveRuntimeState.CLOSED
                self._starting = False
                self._lifecycle_condition.notify_all()
            if isinstance(error, LocalInteractiveRuntimeError):
                raise
            if not isinstance(error, Exception):
                raise
            raise LocalInteractiveRuntimeError(
                "The runtime failed to start."
            ) from error

    @staticmethod
    def _bootstrap_mapping(
        repository: SQLitePrincipalActorMappingRepository,
    ) -> None:
        existing = repository.get(DEVELOPMENT_PRINCIPAL)
        if existing is None:
            repository.create(DEVELOPMENT_PRINCIPAL, DEVELOPMENT_ACTOR)
            return
        if existing != DEVELOPMENT_ACTOR:
            raise LocalInteractiveRuntimeError("The runtime failed to start.")

    @staticmethod
    def _bootstrap_membership(storage: SQLiteLocalStorage) -> None:
        existing = storage.get(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
        if existing is None:
            created = storage.create(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
            if created.status is not MembershipStatus.ACTIVE:
                raise LocalInteractiveRuntimeError("The runtime failed to start.")
            return
        if existing.status is not MembershipStatus.ACTIVE:
            raise LocalInteractiveRuntimeError("The runtime failed to start.")

    @staticmethod
    def _bootstrap_permissions(
        repository: SQLitePermissionGrantRepository,
    ) -> None:
        for action in DEVELOPMENT_PERMISSIONS:
            if not repository.is_granted(
                DEVELOPMENT_ACTOR,
                DEVELOPMENT_WORKSPACE,
                action,
            ):
                repository.create(
                    DEVELOPMENT_ACTOR,
                    DEVELOPMENT_WORKSPACE,
                    action,
                )

    @staticmethod
    def _verify_bootstrap(
        storage: SQLiteLocalStorage,
        mapping_repository: SQLitePrincipalActorMappingRepository,
        permission_repository: SQLitePermissionGrantRepository,
    ) -> None:
        if mapping_repository.get(DEVELOPMENT_PRINCIPAL) != DEVELOPMENT_ACTOR:
            raise LocalInteractiveRuntimeError("The runtime failed to start.")
        membership = storage.get(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
        if membership is None or membership.status is not MembershipStatus.ACTIVE:
            raise LocalInteractiveRuntimeError("The runtime failed to start.")
        if not all(
            permission_repository.is_granted(
                DEVELOPMENT_ACTOR,
                DEVELOPMENT_WORKSPACE,
                action,
            )
            for action in DEVELOPMENT_PERMISSIONS
        ):
            raise LocalInteractiveRuntimeError("The runtime failed to start.")

    def close(self) -> None:
        with self._lifecycle_condition:
            if self._starting:
                self._close_requested = True
                self._development_proof = None
                self._lifecycle_condition.wait_for(lambda: not self._starting)
            if self._state is LocalInteractiveRuntimeState.CLOSED:
                return
            storage = self._storage
            self._storage = None
            self._container = None
            self._gateway = None
            self._csrf_token = None
            self._development_proof = None
            self._state = LocalInteractiveRuntimeState.CLOSED
            self._starting = False

        if storage is not None:
            try:
                storage.close()
            except Exception as error:
                raise LocalInteractiveRuntimeError(
                    "The runtime failed to close."
                ) from error

    def __repr__(self) -> str:
        return (
            "LocalInteractiveRuntime("
            f"database_path={self.database_path!r}, state={self.state.value!r})"
        )
