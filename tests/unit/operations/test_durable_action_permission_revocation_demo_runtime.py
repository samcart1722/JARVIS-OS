"""Runtime proofs for durable action-permission revocation."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.cognition.local_resolution.contracts import (
    PermissionGrantRepositoryError,
)
from app.infrastructure.local_storage import (
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
)
from app.operations.durable_action_permission_revocation_demo_runtime import (
    ACTION,
    ACTOR,
    WORKSPACE,
    revoke_durable_action_permission,
    verify_durable_action_permission_revocation,
)


def test_revoke_phase_closes_storage_and_persists_absence(tmp_path) -> None:
    path = tmp_path / "permission-revocation.sqlite3"

    report = revoke_durable_action_permission(path)

    assert report.success
    assert report.phase == "revoke"
    assert tuple(
        (scenario.scenario_id, scenario.status)
        for scenario in report.scenarios
    ) == (
        ("exact-grant-created-and-allowed", "allowed"),
        ("exact-grant-revoked", "revoked"),
        ("authorization-denied-after-revoke", "denied"),
    )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        repository = SQLitePermissionGrantRepository(
            storage
        )
        assert not repository.is_granted(
            ACTOR,
            WORKSPACE,
            ACTION,
        )


def test_verify_phase_reconstructs_and_proves_denial(tmp_path) -> None:
    path = tmp_path / "permission-revocation.sqlite3"
    revoke_durable_action_permission(path)

    report = verify_durable_action_permission_revocation(
        path
    )

    assert report.success
    assert report.phase == "verify"
    assert tuple(
        (scenario.scenario_id, scenario.status)
        for scenario in report.scenarios
    ) == (
        ("exact-grant-remains-absent", "absent"),
        ("authorization-remains-denied", "denied"),
    )


@pytest.mark.parametrize(
    "operation",
    (
        revoke_durable_action_permission,
        verify_durable_action_permission_revocation,
    ),
)
def test_runtime_rejects_repository_local_database(
    operation,
) -> None:
    repository_path = (
        Path(__file__).resolve().parents[3]
        / "forbidden-revocation.sqlite3"
    )

    with pytest.raises(
        ValueError,
        match="outside the repository",
    ):
        operation(repository_path)

    assert not repository_path.exists()


def test_revoke_failure_aborts_observation_and_closes_storage(
    tmp_path,
) -> None:
    path = tmp_path / "permission-revocation.sqlite3"
    original_is_granted = (
        SQLitePermissionGrantRepository.is_granted
    )
    original_close = SQLiteLocalStorage.close

    with (
        patch.object(
            SQLitePermissionGrantRepository,
            "is_granted",
            autospec=True,
            side_effect=original_is_granted,
        ) as is_granted,
        patch.object(
            SQLitePermissionGrantRepository,
            "revoke",
            autospec=True,
            side_effect=PermissionGrantRepositoryError(
                "Permission grant revocation failed."
            ),
        ),
        patch.object(
            SQLiteLocalStorage,
            "close",
            autospec=True,
            side_effect=original_close,
        ) as close,
    ):
        with pytest.raises(PermissionGrantRepositoryError):
            revoke_durable_action_permission(path)

    assert is_granted.call_count == 1
    assert close.call_count == 1
