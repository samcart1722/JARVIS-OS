"""Tests for the durable principal-to-actor mapping demo runtime."""

from pathlib import Path

import pytest

from app.infrastructure.local_storage import (
    SQLiteLocalStorage,
    SQLitePrincipalActorMappingRepository,
)
from app.operations.durable_principal_actor_mapping_demo_runtime import (
    ACTOR,
    CASE_VARIANT_PRINCIPAL,
    PRIMARY_PRINCIPAL,
    SECONDARY_PRINCIPAL,
    seed_durable_principal_actor_mapping,
    verify_durable_principal_actor_mapping,
)


def test_seed_persists_exact_principal_actor_state(tmp_path) -> None:
    path = tmp_path / "principal-actor.sqlite3"

    report = seed_durable_principal_actor_mapping(path)

    assert report.success
    assert report.phase == "seed"

    assert tuple(
        (scenario.scenario_id, scenario.status)
        for scenario in report.scenarios
    ) == (
        ("primary-mapping-created", "created"),
        ("duplicate-principal-rejected", "conflict_rejected"),
        ("multiple-principals-share-actor", "shared_actor"),
    )

    with SQLiteLocalStorage(path) as storage:
        storage.initialize()
        repository = SQLitePrincipalActorMappingRepository(storage)

        assert repository.get(PRIMARY_PRINCIPAL) == ACTOR
        assert repository.get(SECONDARY_PRINCIPAL) == ACTOR
        assert repository.get(CASE_VARIANT_PRINCIPAL) is None


def test_verify_reconstructs_storage_and_routes_durably(
    tmp_path,
) -> None:
    path = tmp_path / "principal-actor.sqlite3"

    seed_durable_principal_actor_mapping(path)
    report = verify_durable_principal_actor_mapping(path)

    assert report.success
    assert report.phase == "verify"

    assert tuple(
        (scenario.scenario_id, scenario.status)
        for scenario in report.scenarios
    ) == (
        ("primary-durable-routing", "local_success"),
        ("secondary-shared-actor-routing", "local_success"),
        (
            "case-sensitive-mapping-miss",
            "principal_mapping_failed",
        ),
    )

    assert tuple(
        scenario.authenticator_calls
        for scenario in report.scenarios
    ) == (1, 1, 1)

    assert tuple(
        scenario.mapper_calls
        for scenario in report.scenarios
    ) == (1, 1, 1)

    assert tuple(
        scenario.mapping_repository_calls
        for scenario in report.scenarios
    ) == (1, 1, 1)

    assert tuple(
        scenario.membership_calls
        for scenario in report.scenarios
    ) == (1, 1, 0)

    assert tuple(
        scenario.router_calls
        for scenario in report.scenarios
    ) == (1, 1, 0)

    assert tuple(
        scenario.permission_calls
        for scenario in report.scenarios
    ) == (1, 1, 0)

    assert tuple(
        scenario.capability_repository_calls
        for scenario in report.scenarios
    ) == (1, 1, 0)

    assert tuple(
        scenario.cognitive_calls
        for scenario in report.scenarios
    ) == (0, 0, 0)

    assert (
        report.model_calls,
        report.provider_calls,
        report.readiness_calls,
        report.network_calls,
    ) == (0, 0, 0, 0)


def test_runtime_rejects_repository_local_database() -> None:
    repository_path = (
        Path(__file__).resolve().parents[3]
        / "forbidden-principal-actor.sqlite3"
    )

    with pytest.raises(
        ValueError,
        match="outside the repository",
    ):
        seed_durable_principal_actor_mapping(repository_path)

    assert not repository_path.exists()
