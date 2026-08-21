"""Tests for durable action-permission demo runtime."""

from pathlib import Path

import pytest

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
    SQLitePrincipalActorMappingRepository,
)
from app.membership import MembershipStatus
from app.operations.durable_action_permission_demo_runtime import (
    ACTOR,
    LIST_ID,
    LIST_ITEM,
    OTHER_ACTOR,
    OTHER_WORKSPACE,
    PRIMARY_PRINCIPAL,
    SECONDARY_PRINCIPAL,
    WORKSPACE,
    seed_durable_action_permission,
    verify_durable_action_permission,
)


def test_seed_persists_exact_durable_authorization_state(
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "durable-action-permission.sqlite3"
    )

    report = seed_durable_action_permission(
        path
    )

    assert report.success
    assert report.phase == "seed"

    assert tuple(
        (
            scenario.scenario_id,
            scenario.status,
        )
        for scenario in report.scenarios
    ) == (
        (
            "durable-identity-membership-seeded",
            "seeded",
        ),
        (
            "exact-permission-created",
            "created",
        ),
        (
            "duplicate-permission-rejected",
            "conflict_rejected",
        ),
        (
            "permission-boundary-is-exact",
            "exact",
        ),
        (
            "durable-list-seeded",
            "seeded",
        ),
    )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()

        mapping_repository = (
            SQLitePrincipalActorMappingRepository(
                storage
            )
        )

        permission_repository = (
            SQLitePermissionGrantRepository(
                storage
            )
        )

        assert mapping_repository.get(
            PRIMARY_PRINCIPAL
        ) == ACTOR

        assert mapping_repository.get(
            SECONDARY_PRINCIPAL
        ) == OTHER_ACTOR

        assert (
            storage.get(
                ACTOR,
                WORKSPACE,
            ).status
            is MembershipStatus.ACTIVE
        )

        assert (
            storage.get(
                ACTOR,
                OTHER_WORKSPACE,
            ).status
            is MembershipStatus.ACTIVE
        )

        assert (
            storage.get(
                OTHER_ACTOR,
                WORKSPACE,
            ).status
            is MembershipStatus.ACTIVE
        )

        assert permission_repository.is_granted(
            ACTOR,
            WORKSPACE,
            LIST_ITEMS_READ,
        )

        assert not permission_repository.is_granted(
            ActorIdentity(
                "Durable-Permission-Actor"
            ),
            WORKSPACE,
            LIST_ITEMS_READ,
        )

        assert not permission_repository.is_granted(
            ACTOR,
            WorkspaceIdentity(
                "Durable-Permission-Workspace"
            ),
            LIST_ITEMS_READ,
        )

        assert not permission_repository.is_granted(
            ACTOR,
            WORKSPACE,
            "LIST.ITEMS.READ",
        )

        assert not permission_repository.is_granted(
            ACTOR,
            WORKSPACE,
            LIST_ITEMS_ADD,
        )

        assert storage.read(
            WORKSPACE,
            LIST_ID,
        ).items == (
            LIST_ITEM,
        )


def test_verify_reconstructs_full_durable_authorization_path(
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "durable-action-permission.sqlite3"
    )

    seed_durable_action_permission(
        path
    )

    report = verify_durable_action_permission(
        path
    )

    assert report.success
    assert report.phase == "verify"

    assert tuple(
        (
            scenario.scenario_id,
            scenario.status,
        )
        for scenario in report.scenarios
    ) == (
        (
            "exact-durable-permission-success",
            "local_success",
        ),
        (
            "wrong-workspace-denied",
            "local_permission_denied",
        ),
        (
            "wrong-action-denied",
            "local_permission_denied",
        ),
        (
            "wrong-actor-denied",
            "local_permission_denied",
        ),
        (
            "permission-repository-failure-denied",
            "local_permission_denied",
        ),
    )

    assert tuple(
        scenario.authenticator_calls
        for scenario in report.scenarios
    ) == (
        1,
        1,
        1,
        1,
        1,
    )

    assert tuple(
        scenario.mapper_calls
        for scenario in report.scenarios
    ) == (
        1,
        1,
        1,
        1,
        1,
    )

    assert tuple(
        scenario.mapping_repository_calls
        for scenario in report.scenarios
    ) == (
        1,
        1,
        1,
        1,
        1,
    )

    assert tuple(
        scenario.membership_calls
        for scenario in report.scenarios
    ) == (
        1,
        1,
        1,
        1,
        1,
    )

    assert tuple(
        scenario.router_calls
        for scenario in report.scenarios
    ) == (
        1,
        1,
        1,
        1,
        1,
    )

    assert tuple(
        scenario.permission_repository_calls
        for scenario in report.scenarios
    ) == (
        1,
        1,
        1,
        1,
        1,
    )

    assert tuple(
        scenario.list_read_calls
        for scenario in report.scenarios
    ) == (
        1,
        0,
        0,
        0,
        0,
    )

    assert tuple(
        scenario.list_add_calls
        for scenario in report.scenarios
    ) == (
        0,
        0,
        0,
        0,
        0,
    )

    assert tuple(
        scenario.cognitive_calls
        for scenario in report.scenarios
    ) == (
        0,
        0,
        0,
        0,
        0,
    )

    assert (
        report.model_calls,
        report.provider_calls,
        report.readiness_calls,
        report.network_calls,
    ) == (
        0,
        0,
        0,
        0,
    )


def test_runtime_rejects_repository_local_database(
) -> None:
    repository_path = (
        Path(__file__).resolve().parents[3]
        / "forbidden-durable-permission.sqlite3"
    )

    with pytest.raises(
        ValueError,
        match="outside the repository",
    ):
        seed_durable_action_permission(
            repository_path
        )

    assert not repository_path.exists()
