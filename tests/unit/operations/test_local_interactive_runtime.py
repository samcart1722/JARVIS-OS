import sqlite3
from pathlib import Path
from threading import Event, Thread, current_thread

import pytest

from app.cognition.local_resolution.models import ActorIdentity
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    RepositoryPermissionPolicy,
)
from app.core.container import container as default_container
from app.infrastructure.local_storage.sqlite_storage import (
    SCHEMA_VERSION,
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
    SQLitePrincipalActorMappingRepository,
)
from app.local_command import LocalCommandApplicationGateway
from app.membership import MembershipStatus
from app.operations.local_interactive_runtime import (
    DEVELOPMENT_ACTOR,
    DEVELOPMENT_PERMISSIONS,
    DEVELOPMENT_PRINCIPAL,
    DEVELOPMENT_WORKSPACE,
    LocalInteractiveRuntime,
    LocalInteractiveRuntimeError,
    LocalInteractiveRuntimeState,
)
from app.principal_authentication import (
    ConfiguredLocalPrincipalAuthenticator,
    LocalAuthenticationProof,
    RejectingLocalPrincipalAuthenticator,
)
from app.principal_authentication.models import PrincipalAuthenticationErrorCode

TEST_PROOF = "sprint34-b1-test-proof"


def _runtime(path: Path, proof: str = TEST_PROOF) -> LocalInteractiveRuntime:
    return LocalInteractiveRuntime(path, proof)


def _initialized_storage(path: Path) -> SQLiteLocalStorage:
    storage = SQLiteLocalStorage(path)
    storage.open()
    storage.initialize()
    return storage


def test_construction_is_no_io_secret_safe_and_new(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    runtime = _runtime(path)

    assert runtime.state is LocalInteractiveRuntimeState.NEW
    assert runtime.database_path == path
    assert not path.exists()
    assert TEST_PROOF not in repr(runtime)
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        runtime.gateway
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        runtime.csrf_token


def test_start_builds_schema_bootstrap_gateway_and_csrf(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    runtime = _runtime(path)
    runtime.start()

    assert runtime.state is LocalInteractiveRuntimeState.STARTED
    assert type(runtime.gateway) is LocalCommandApplicationGateway
    assert isinstance(runtime.csrf_token, str)
    assert runtime.csrf_token
    assert runtime._container.local_command_application_gateway is runtime.gateway

    runtime.close()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION


def test_exact_bootstrap_is_created_and_no_extra_permission_exists(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    runtime = _runtime(path)
    runtime.start()
    runtime.close()

    with _initialized_storage(path) as storage:
        mapping = SQLitePrincipalActorMappingRepository(storage)
        permission = SQLitePermissionGrantRepository(storage)
        assert mapping.get(DEVELOPMENT_PRINCIPAL) == DEVELOPMENT_ACTOR
        membership = storage.get(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
        assert membership is not None
        assert membership.status is MembershipStatus.ACTIVE
        assert DEVELOPMENT_PERMISSIONS == (
            LIST_ITEMS_ADD,
            LIST_ITEMS_READ,
            KNOWLEDGE_RECORDS_ADD,
            KNOWLEDGE_RECORDS_READ,
        )
        assert all(
            permission.is_granted(
                DEVELOPMENT_ACTOR,
                DEVELOPMENT_WORKSPACE,
                action,
            )
            for action in DEVELOPMENT_PERMISSIONS
        )
        assert not permission.is_granted(
            DEVELOPMENT_ACTOR,
            DEVELOPMENT_WORKSPACE,
            "admin.all",
        )


def test_exact_existing_bootstrap_is_idempotently_accepted(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    first = _runtime(path)
    first.start()
    first.close()

    second = _runtime(path)
    second.start()
    assert second.state is LocalInteractiveRuntimeState.STARTED
    second.close()

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM principal_actor_mappings"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM actor_workspace_memberships"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM action_permission_grants"
        ).fetchone()[0] == 4


def test_conflicting_mapping_fails_closed_and_cannot_restart(tmp_path: Path) -> None:
    path = tmp_path / "runtime.sqlite3"
    with _initialized_storage(path) as storage:
        SQLitePrincipalActorMappingRepository(storage).create(
            DEVELOPMENT_PRINCIPAL,
            ActorIdentity("unexpected-actor"),
        )

    runtime = _runtime(path)
    with pytest.raises(LocalInteractiveRuntimeError, match="start") as captured:
        runtime.start()

    assert TEST_PROOF not in str(captured.value)
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    with pytest.raises(LocalInteractiveRuntimeError):
        runtime.gateway
    with pytest.raises(LocalInteractiveRuntimeError):
        runtime.csrf_token
    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        runtime.start()


def test_inactive_membership_fails_closed_without_reactivation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    with _initialized_storage(path) as storage:
        SQLitePrincipalActorMappingRepository(storage).create(
            DEVELOPMENT_PRINCIPAL,
            DEVELOPMENT_ACTOR,
        )
        storage.create(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
        storage.deactivate(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)

    runtime = _runtime(path)
    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        runtime.start()

    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    with _initialized_storage(path) as storage:
        membership = storage.get(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
        assert membership is not None
        assert membership.status is MembershipStatus.INACTIVE


def test_existing_permissions_are_accepted_and_missing_are_created(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    with _initialized_storage(path) as storage:
        permission = SQLitePermissionGrantRepository(storage)
        permission.create(
            DEVELOPMENT_ACTOR,
            DEVELOPMENT_WORKSPACE,
            LIST_ITEMS_ADD,
        )

    runtime = _runtime(path)
    runtime.start()
    runtime.close()

    with sqlite3.connect(path) as connection:
        actions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT action FROM action_permission_grants ORDER BY action"
            ).fetchall()
        )
    assert actions == tuple(sorted(DEVELOPMENT_PERMISSIONS))


def test_one_storage_backs_every_durable_runtime_repository(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path / "runtime.sqlite3")
    runtime.start()

    storage = runtime._storage
    current = runtime._container
    assert current.local_list_repository is storage
    assert current.membership_repository is storage
    assert current.local_knowledge_repository._storage is storage
    assert current.local_permission_grant_repository._storage is storage
    assert current.principal_actor_mapper._repository._storage is storage

    runtime.close()


def test_runtime_container_uses_durable_security_and_configured_auth(
    tmp_path: Path,
) -> None:
    runtime = _runtime(tmp_path / "runtime.sqlite3")
    runtime.start()
    current = runtime._container

    assert type(current.local_principal_authenticator) is (
        ConfiguredLocalPrincipalAuthenticator
    )
    authenticated = current.local_principal_authenticator.authenticate(
        LocalAuthenticationProof(TEST_PROOF)
    )
    rejected = current.local_principal_authenticator.authenticate(
        LocalAuthenticationProof("wrong-proof")
    )
    assert authenticated.success
    assert authenticated.principal.principal == DEVELOPMENT_PRINCIPAL
    assert not rejected.success
    assert rejected.error_code is PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED
    assert isinstance(current.local_permission_policy, RepositoryPermissionPolicy)
    assert current._settings.REASONING_ENABLED is False

    runtime.close()


def test_list_and_knowledge_repositories_are_durable_adapters(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path / "runtime.sqlite3")
    runtime.start()

    assert runtime._container.local_list_repository is runtime._storage
    assert runtime._container.local_knowledge_repository._storage is runtime._storage

    runtime.close()


def test_csrf_is_runtime_local_and_unavailable_after_close(tmp_path: Path) -> None:
    first = _runtime(tmp_path / "first.sqlite3")
    second = _runtime(tmp_path / "second.sqlite3")
    first.start()
    second.start()

    assert first.csrf_token != second.csrf_token
    first.close()
    second.close()
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        first.csrf_token


def test_second_start_start_after_close_and_close_before_start(tmp_path: Path) -> None:
    started = _runtime(tmp_path / "started.sqlite3")
    started.start()
    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        started.start()
    started.close()
    started.close()
    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        started.start()

    never_started = _runtime(tmp_path / "closed.sqlite3")
    never_started.close()
    never_started.close()
    assert never_started.state is LocalInteractiveRuntimeState.CLOSED
    assert not (tmp_path / "closed.sqlite3").exists()
    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        never_started.start()


def test_close_clears_gateway_container_csrf_and_storage(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path / "runtime.sqlite3")
    runtime.start()
    owned_storage = runtime._storage
    runtime.close()

    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    assert not owned_storage.is_open
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        runtime.gateway
    assert runtime._container is None
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        runtime.csrf_token


def test_simulated_initialize_failure_closes_partial_storage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import app.operations.local_interactive_runtime as runtime_module

    observed = {}

    class FailingStorage:
        def __init__(self, path):
            self.path = path
            self.is_open = False
            self.closed = False
            observed["storage"] = self

        def open(self):
            self.is_open = True

        def initialize(self):
            raise RuntimeError("private storage detail")

        def close(self):
            self.is_open = False
            self.closed = True

    monkeypatch.setattr(runtime_module, "SQLiteLocalStorage", FailingStorage)
    runtime = _runtime(tmp_path / "runtime.sqlite3")

    with pytest.raises(LocalInteractiveRuntimeError, match="start") as captured:
        runtime.start()

    assert "private storage detail" not in str(captured.value)
    assert TEST_PROOF not in str(captured.value)
    assert observed["storage"].closed
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    with pytest.raises(LocalInteractiveRuntimeError):
        runtime.start()


def test_reentrant_start_fails_and_closes_partial_storage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import app.operations.local_interactive_runtime as runtime_module

    real_storage = runtime_module.SQLiteLocalStorage
    runtime = _runtime(tmp_path / "runtime.sqlite3")
    observed = {}

    class ReentrantStorage(real_storage):
        def initialize(self):
            with pytest.raises(LocalInteractiveRuntimeError, match="start"):
                runtime.start()
            observed["reentrant_rejected"] = True
            raise RuntimeError("force outer startup failure")

    monkeypatch.setattr(runtime_module, "SQLiteLocalStorage", ReentrantStorage)

    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        runtime.start()

    assert observed == {"reentrant_rejected": True}
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    with pytest.raises(LocalInteractiveRuntimeError):
        runtime.start()


def test_close_during_start_cancels_before_publication_and_waits_for_cleanup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import app.operations.local_interactive_runtime as runtime_module

    real_storage = runtime_module.SQLiteLocalStorage
    startup_paused = Event()
    release_startup = Event()
    start_errors = []
    close_errors = []
    observed = {}

    class PausingStorage(real_storage):
        def open(self):
            observed["open_thread"] = current_thread()
            return super().open()

        def initialize(self):
            super().initialize()
            startup_paused.set()
            assert release_startup.wait(timeout=5)

        def close(self):
            observed["close_thread"] = current_thread()
            return super().close()

    monkeypatch.setattr(runtime_module, "SQLiteLocalStorage", PausingStorage)
    runtime = _runtime(tmp_path / "runtime.sqlite3")

    def start_runtime() -> None:
        try:
            runtime.start()
        except BaseException as error:
            start_errors.append(error)

    def close_runtime() -> None:
        try:
            runtime.close()
        except BaseException as error:
            close_errors.append(error)

    start_thread = Thread(target=start_runtime)
    close_thread = Thread(target=close_runtime)
    start_thread.start()
    assert startup_paused.wait(timeout=5)
    close_thread.start()

    with runtime._lifecycle_condition:
        assert runtime._lifecycle_condition.wait_for(
            lambda: runtime._close_requested,
            timeout=5,
        )
    assert close_thread.is_alive()
    assert runtime.state is LocalInteractiveRuntimeState.NEW
    assert runtime._storage is None

    release_startup.set()
    start_thread.join(timeout=5)
    close_thread.join(timeout=5)

    assert not start_thread.is_alive()
    assert not close_thread.is_alive()
    assert len(start_errors) == 1
    assert type(start_errors[0]) is LocalInteractiveRuntimeError
    assert str(start_errors[0]) == "The runtime cannot start."
    assert close_errors == []
    assert observed["close_thread"] is observed["open_thread"]
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    assert runtime._container is None
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        runtime.gateway
    with pytest.raises(LocalInteractiveRuntimeError, match="unavailable"):
        runtime.csrf_token
    with pytest.raises(LocalInteractiveRuntimeError, match="start"):
        runtime.start()


def test_simulated_container_failure_closes_initialized_storage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import app.operations.local_interactive_runtime as runtime_module

    class FailingContainer:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            raise RuntimeError("private composition detail")

    monkeypatch.setattr(runtime_module, "Container", FailingContainer)
    runtime = _runtime(tmp_path / "runtime.sqlite3")

    with pytest.raises(LocalInteractiveRuntimeError, match="start") as captured:
        runtime.start()

    assert "private composition detail" not in str(captured.value)
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert runtime._storage is None
    with pytest.raises(LocalInteractiveRuntimeError):
        runtime.gateway
    with pytest.raises(LocalInteractiveRuntimeError):
        runtime.csrf_token


def test_proof_is_not_persisted_and_default_container_is_unchanged(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runtime.sqlite3"
    default_authenticator = default_container.local_principal_authenticator
    default_gateway = default_container.local_command_application_gateway
    assert type(default_authenticator) is RejectingLocalPrincipalAuthenticator

    runtime = _runtime(path)
    runtime.start()
    runtime.close()

    assert TEST_PROOF.encode() not in path.read_bytes()
    assert default_container.local_principal_authenticator is default_authenticator
    assert default_container.local_command_application_gateway is default_gateway
    denied = default_authenticator.authenticate(LocalAuthenticationProof(TEST_PROOF))
    assert not denied.success


@pytest.mark.parametrize("proof", ("", "   ", None, object()))
def test_constructor_rejects_invalid_proof_without_disclosure(
    tmp_path: Path,
    proof,
) -> None:
    with pytest.raises(ValueError) as captured:
        LocalInteractiveRuntime(tmp_path / "runtime.sqlite3", proof)
    assert repr(proof) not in str(captured.value)


@pytest.mark.parametrize("path", ("", "   ", ".", ".."))
def test_constructor_rejects_invalid_database_path(path) -> None:
    with pytest.raises(ValueError):
        LocalInteractiveRuntime(path, TEST_PROOF)
