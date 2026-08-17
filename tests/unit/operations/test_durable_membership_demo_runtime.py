"""Runtime proofs for durable actor-workspace membership."""

from pathlib import Path

import pytest

from app.infrastructure.local_storage import SQLiteLocalStorage
from app.membership import MembershipStatus
from app.operations.durable_membership_demo_runtime import (
    ACTIVE_ACTOR,
    INACTIVE_ACTOR,
    NO_GRANT_ACTOR,
    NON_MEMBER_ACTOR,
    PRIMARY_WORKSPACE,
    seed_durable_membership,
    verify_durable_membership,
)


def test_seed_closes_storage_and_establishes_exact_membership_state(tmp_path) -> None:
    path = tmp_path / "membership.sqlite3"
    report = seed_durable_membership(path)
    assert report.success and report.phase == "seed"
    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        assert (
            storage.get(ACTIVE_ACTOR, PRIMARY_WORKSPACE).status
            is MembershipStatus.ACTIVE
        )
        assert (
            storage.get(INACTIVE_ACTOR, PRIMARY_WORKSPACE).status
            is MembershipStatus.INACTIVE
        )
        assert (
            storage.get(NO_GRANT_ACTOR, PRIMARY_WORKSPACE).status
            is MembershipStatus.ACTIVE
        )
        assert storage.get(NON_MEMBER_ACTOR, PRIMARY_WORKSPACE) is None


def test_verify_reconstructs_storage_and_proves_all_boundaries(tmp_path) -> None:
    path = tmp_path / "membership.sqlite3"
    seed_durable_membership(path)
    report = verify_durable_membership(path)
    assert report.success and report.phase == "verify"
    assert tuple((item.scenario_id, item.status) for item in report.scenarios) == (
        ("active-permitted", "local_success"),
        ("non-member", "membership_not_found"),
        ("inactive-member", "membership_inactive"),
        ("active-no-grant", "local_permission_denied"),
        ("workspace-isolation", "membership_not_found"),
        ("payload-workspace-override", "invalid_knowledge_fields"),
    )
    assert tuple(item.router_calls for item in report.scenarios) == (1, 0, 0, 1, 0, 1)
    assert tuple(item.permission_calls for item in report.scenarios) == (
        1, 0, 0, 1, 0, 0
    )
    assert tuple(item.repository_calls for item in report.scenarios) == (
        1, 0, 0, 0, 0, 0
    )
    assert (report.model_calls, report.provider_calls) == (0, 0)
    assert (report.readiness_calls, report.network_calls) == (0, 0)


def test_runtime_rejects_repository_local_database() -> None:
    repository_path = Path(__file__).resolve().parents[3] / "forbidden.sqlite3"
    with pytest.raises(ValueError, match="outside the repository"):
        seed_durable_membership(repository_path)
    assert not repository_path.exists()
