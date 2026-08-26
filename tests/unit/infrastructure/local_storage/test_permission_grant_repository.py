"""Durable exact action-permission repository behavior."""

import sqlite3

import pytest

from app.cognition.local_resolution.contracts import (
    PermissionGrantConflict,
    PermissionGrantRepositoryError,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
)
from app.infrastructure.local_storage import (
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
)


def test_permission_repository_requires_storage() -> None:
    with pytest.raises(
        ValueError,
        match="local storage",
    ):
        SQLitePermissionGrantRepository(None)


def test_permission_grant_is_durable_exact_and_case_sensitive(
    tmp_path,
) -> None:
    path = tmp_path / "permissions.sqlite3"

    actor = ActorIdentity("Actor")
    workspace = WorkspaceIdentity("Workspace")

    with SQLiteLocalStorage(path) as first:
        first.initialize()

        repository = SQLitePermissionGrantRepository(
            first
        )

        assert not repository.is_granted(
            actor,
            workspace,
            LIST_ITEMS_READ,
        )

        assert (
            repository.create(
                actor,
                workspace,
                LIST_ITEMS_READ,
            )
            is None
        )

        assert repository.is_granted(
            actor,
            workspace,
            LIST_ITEMS_READ,
        )

        assert not repository.is_granted(
            ActorIdentity("actor"),
            workspace,
            LIST_ITEMS_READ,
        )

        assert not repository.is_granted(
            actor,
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
        )

        assert not repository.is_granted(
            actor,
            workspace,
            "LIST.ITEMS.READ",
        )

        assert not repository.is_granted(
            actor,
            workspace,
            " list.items.read ",
        )

        with pytest.raises(
            PermissionGrantConflict,
            match="already exists",
        ):
            repository.create(
                actor,
                workspace,
                LIST_ITEMS_READ,
            )

    with SQLiteLocalStorage(path) as second:
        second.initialize()

        repository = SQLitePermissionGrantRepository(
            second
        )

        assert repository.is_granted(
            actor,
            workspace,
            LIST_ITEMS_READ,
        )

        assert not repository.is_granted(
            ActorIdentity("actor"),
            workspace,
            LIST_ITEMS_READ,
        )


def test_permission_dimensions_remain_independent(
    tmp_path,
) -> None:
    path = tmp_path / "independent.sqlite3"

    actor = ActorIdentity("actor")
    other_actor = ActorIdentity("other-actor")

    workspace = WorkspaceIdentity("workspace")
    other_workspace = WorkspaceIdentity(
        "other-workspace"
    )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        repository = SQLitePermissionGrantRepository(
            storage
        )

        repository.create(
            actor,
            workspace,
            LIST_ITEMS_READ,
        )

        repository.create(
            actor,
            workspace,
            LIST_ITEMS_ADD,
        )

        repository.create(
            actor,
            other_workspace,
            LIST_ITEMS_READ,
        )

        repository.create(
            other_actor,
            workspace,
            LIST_ITEMS_READ,
        )

        assert repository.is_granted(
            actor,
            workspace,
            LIST_ITEMS_READ,
        )

        assert repository.is_granted(
            actor,
            workspace,
            LIST_ITEMS_ADD,
        )

        assert repository.is_granted(
            actor,
            other_workspace,
            LIST_ITEMS_READ,
        )

        assert repository.is_granted(
            other_actor,
            workspace,
            LIST_ITEMS_READ,
        )


def test_permission_action_is_stored_without_normalization(
    tmp_path,
) -> None:
    path = tmp_path / "exact-action.sqlite3"

    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    exact_action = " list.items.read "

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        repository = SQLitePermissionGrantRepository(
            storage
        )

        repository.create(
            actor,
            workspace,
            exact_action,
        )

        assert repository.is_granted(
            actor,
            workspace,
            exact_action,
        )

        assert not repository.is_granted(
            actor,
            workspace,
            LIST_ITEMS_READ,
        )


@pytest.mark.parametrize(
    ("method_name", "actor", "workspace", "action", "message"),
    (
        (
            "is_granted",
            "actor",
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
            "actor",
        ),
        (
            "create",
            "actor",
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
            "actor",
        ),
        (
            "is_granted",
            ActorIdentity("actor"),
            "workspace",
            LIST_ITEMS_READ,
            "workspace",
        ),
        (
            "create",
            ActorIdentity("actor"),
            "workspace",
            LIST_ITEMS_READ,
            "workspace",
        ),
        (
            "is_granted",
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            None,
            "action",
        ),
        (
            "create",
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            " ",
            "action",
        ),
    ),
)
def test_permission_repository_requires_exact_boundary_values(
    method_name,
    actor,
    workspace,
    action,
    message,
    tmp_path,
) -> None:
    with SQLiteLocalStorage(
        tmp_path / f"{method_name}.sqlite3"
    ) as storage:
        storage.initialize()

        repository = SQLitePermissionGrantRepository(
            storage
        )

        method = getattr(
            repository,
            method_name,
        )

        with pytest.raises(
            ValueError,
            match=message,
        ):
            method(
                actor,
                workspace,
                action,
            )


def test_permission_repository_read_failure_is_safe(
    tmp_path,
) -> None:
    path = tmp_path / "read-failure.sqlite3"

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        repository = SQLitePermissionGrantRepository(
            storage
        )

        storage._connection.execute(
            "DROP TABLE action_permission_grants"
        )

        with pytest.raises(
            PermissionGrantRepositoryError,
            match="read failed",
        ):
            repository.is_granted(
                ActorIdentity("actor"),
                WorkspaceIdentity("workspace"),
                LIST_ITEMS_READ,
            )


def test_permission_repository_write_failure_is_safe_and_rolls_back(
    tmp_path,
) -> None:
    path = tmp_path / "write-failure.sqlite3"

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        repository = SQLitePermissionGrantRepository(
            storage
        )

        storage._connection.execute(
            "CREATE TRIGGER fail_permission_insert "
            "BEFORE INSERT "
            "ON action_permission_grants "
            "BEGIN "
            "SELECT RAISE("
            "ABORT, 'forced permission failure'"
            "); "
            "END"
        )

        with pytest.raises(
            PermissionGrantRepositoryError,
            match="write failed",
        ):
            repository.create(
                ActorIdentity("actor"),
                WorkspaceIdentity("workspace"),
                LIST_ITEMS_READ,
            )

        assert not storage._connection.in_transaction

        assert storage._connection.execute(
            "SELECT count(*) "
            "FROM action_permission_grants"
        ).fetchone() == (
            0,
        )


def test_database_constraint_rejects_null_permission_components(
    tmp_path,
) -> None:
    path = tmp_path / "constraints.sqlite3"

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

    with sqlite3.connect(path) as connection:
        for values in (
            (
                None,
                "workspace",
                LIST_ITEMS_READ,
            ),
            (
                "actor",
                None,
                LIST_ITEMS_READ,
            ),
            (
                "actor",
                "workspace",
                None,
            ),
        ):
            with pytest.raises(
                sqlite3.IntegrityError
            ):
                connection.execute(
                    "INSERT INTO "
                    "action_permission_grants "
                    "(actor_id, workspace_id, action) "
                    "VALUES (?, ?, ?)",
                    values,
                )


def test_permission_revoke_is_exact_idempotent_and_allows_regrant(
    tmp_path,
) -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    with SQLiteLocalStorage(
        tmp_path / "revoke-lifecycle.sqlite3"
    ) as storage:
        storage.initialize()
        repository = SQLitePermissionGrantRepository(storage)

        repository.create(actor, workspace, LIST_ITEMS_READ)
        assert repository.is_granted(actor, workspace, LIST_ITEMS_READ)

        assert repository.revoke(actor, workspace, LIST_ITEMS_READ) is None
        assert not repository.is_granted(actor, workspace, LIST_ITEMS_READ)

        assert repository.revoke(actor, workspace, LIST_ITEMS_READ) is None
        assert repository.revoke(actor, workspace, LIST_ITEMS_READ) is None
        assert not repository.is_granted(actor, workspace, LIST_ITEMS_READ)

        repository.create(actor, workspace, LIST_ITEMS_READ)
        assert repository.is_granted(actor, workspace, LIST_ITEMS_READ)


def test_permission_revoke_preserves_unrelated_grants(
    tmp_path,
) -> None:
    actor = ActorIdentity("actor")
    other_actor = ActorIdentity("other-actor")
    workspace = WorkspaceIdentity("workspace")
    other_workspace = WorkspaceIdentity("other-workspace")

    with SQLiteLocalStorage(
        tmp_path / "revoke-isolation.sqlite3"
    ) as storage:
        storage.initialize()
        repository = SQLitePermissionGrantRepository(storage)

        for grant in (
            (actor, workspace, LIST_ITEMS_READ),
            (other_actor, workspace, LIST_ITEMS_READ),
            (actor, other_workspace, LIST_ITEMS_READ),
            (actor, workspace, LIST_ITEMS_ADD),
        ):
            repository.create(*grant)

        repository.revoke(actor, workspace, LIST_ITEMS_READ)

        assert not repository.is_granted(actor, workspace, LIST_ITEMS_READ)
        assert repository.is_granted(other_actor, workspace, LIST_ITEMS_READ)
        assert repository.is_granted(actor, other_workspace, LIST_ITEMS_READ)
        assert repository.is_granted(actor, workspace, LIST_ITEMS_ADD)


def test_permission_revoke_is_case_sensitive_and_does_not_normalize(
    tmp_path,
) -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")
    exact_action = " list.items.read "

    with SQLiteLocalStorage(
        tmp_path / "revoke-exactness.sqlite3"
    ) as storage:
        storage.initialize()
        repository = SQLitePermissionGrantRepository(storage)

        repository.create(actor, workspace, exact_action)

        repository.revoke(actor, workspace, " LIST.ITEMS.READ ")
        assert repository.is_granted(actor, workspace, exact_action)

        repository.revoke(actor, workspace, LIST_ITEMS_READ)
        assert repository.is_granted(actor, workspace, exact_action)

        repository.revoke(actor, workspace, exact_action)
        assert not repository.is_granted(actor, workspace, exact_action)


@pytest.mark.parametrize(
    ("actor", "workspace", "action", "message"),
    (
        (
            "actor",
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
            "actor",
        ),
        (
            ActorIdentity("actor"),
            "workspace",
            LIST_ITEMS_READ,
            "workspace",
        ),
        (
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            None,
            "action",
        ),
        (
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            "",
            "action",
        ),
        (
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            " ",
            "action",
        ),
    ),
)
def test_permission_revoke_requires_exact_boundary_values(
    actor,
    workspace,
    action,
    message,
    tmp_path,
) -> None:
    with SQLiteLocalStorage(
        tmp_path / "invalid-revoke.sqlite3"
    ) as storage:
        storage.initialize()
        repository = SQLitePermissionGrantRepository(storage)

        with pytest.raises(ValueError, match=message):
            repository.revoke(actor, workspace, action)


def test_permission_revoke_survives_close_and_reopen(
    tmp_path,
) -> None:
    path = tmp_path / "durable-revoke.sqlite3"
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    with SQLiteLocalStorage(path) as first:
        first.initialize()
        repository = SQLitePermissionGrantRepository(first)
        repository.create(actor, workspace, LIST_ITEMS_READ)
        repository.revoke(actor, workspace, LIST_ITEMS_READ)

    with SQLiteLocalStorage(path) as second:
        second.initialize()
        repository = SQLitePermissionGrantRepository(second)
        assert not repository.is_granted(actor, workspace, LIST_ITEMS_READ)


def test_permission_revoke_failure_is_safe_and_rolls_back(
    tmp_path,
) -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    with SQLiteLocalStorage(
        tmp_path / "revoke-failure.sqlite3"
    ) as storage:
        storage.initialize()
        repository = SQLitePermissionGrantRepository(storage)
        repository.create(actor, workspace, LIST_ITEMS_READ)

        storage._connection.execute(
            "CREATE TRIGGER fail_permission_delete "
            "BEFORE DELETE "
            "ON action_permission_grants "
            "BEGIN "
            "SELECT RAISE("
            "ABORT, 'forced permission failure'"
            "); "
            "END"
        )

        with pytest.raises(PermissionGrantRepositoryError):
            repository.revoke(actor, workspace, LIST_ITEMS_READ)

        assert not storage._connection.in_transaction
        assert repository.is_granted(actor, workspace, LIST_ITEMS_READ)
