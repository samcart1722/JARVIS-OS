"""Bounded proof of durable local action-permission revocation."""

from dataclasses import dataclass
from pathlib import Path

from app.cognition.local_resolution.models import (
    ActorIdentity,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    RepositoryPermissionPolicy,
)
from app.infrastructure.local_storage import (
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
)

ACTOR = ActorIdentity(
    "durable-permission-revocation-actor"
)

WORKSPACE = WorkspaceIdentity(
    "durable-permission-revocation-workspace"
)

ACTION = "list.items.read"

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class DurableActionPermissionRevocationScenarioReport:
    scenario_id: str
    status: str
    passed: bool


@dataclass(frozen=True, slots=True)
class DurableActionPermissionRevocationDemoReport:
    phase: str
    scenarios: tuple[
        DurableActionPermissionRevocationScenarioReport,
        ...,
    ]

    @property
    def success(self) -> bool:
        return all(
            scenario.passed
            for scenario in self.scenarios
        )


def _require_external_database(
    database_path: Path,
) -> Path:
    path = database_path.resolve()

    if (
        path == REPOSITORY_ROOT
        or REPOSITORY_ROOT in path.parents
    ):
        raise ValueError(
            "Demo database must be outside the repository."
        )

    return path


def revoke_durable_action_permission(
    database_path: Path,
) -> DurableActionPermissionRevocationDemoReport:
    reports = []

    with SQLiteLocalStorage(
        _require_external_database(database_path)
    ) as storage:
        storage.initialize()
        permission_repository = (
            SQLitePermissionGrantRepository(storage)
        )
        policy = RepositoryPermissionPolicy(
            permission_repository
        )

        permission_repository.create(
            ACTOR,
            WORKSPACE,
            ACTION,
        )
        allowed = policy.is_allowed(
            ACTOR,
            WORKSPACE,
            ACTION,
        )
        reports.append(
            DurableActionPermissionRevocationScenarioReport(
                scenario_id="exact-grant-created-and-allowed",
                status="allowed" if allowed else "denied",
                passed=allowed,
            )
        )

        revoke_result = permission_repository.revoke(
            ACTOR,
            WORKSPACE,
            ACTION,
        )
        reports.append(
            DurableActionPermissionRevocationScenarioReport(
                scenario_id="exact-grant-revoked",
                status="revoked",
                passed=revoke_result is None,
            )
        )

        denied = not policy.is_allowed(
            ACTOR,
            WORKSPACE,
            ACTION,
        )
        reports.append(
            DurableActionPermissionRevocationScenarioReport(
                scenario_id="authorization-denied-after-revoke",
                status="denied" if denied else "allowed",
                passed=denied,
            )
        )

    return DurableActionPermissionRevocationDemoReport(
        phase="revoke",
        scenarios=tuple(reports),
    )


def verify_durable_action_permission_revocation(
    database_path: Path,
) -> DurableActionPermissionRevocationDemoReport:
    reports = []

    with SQLiteLocalStorage(
        _require_external_database(database_path)
    ) as storage:
        storage.initialize()
        permission_repository = (
            SQLitePermissionGrantRepository(storage)
        )
        policy = RepositoryPermissionPolicy(
            permission_repository
        )

        absent = not permission_repository.is_granted(
            ACTOR,
            WORKSPACE,
            ACTION,
        )
        reports.append(
            DurableActionPermissionRevocationScenarioReport(
                scenario_id="exact-grant-remains-absent",
                status="absent" if absent else "present",
                passed=absent,
            )
        )

        denied = not policy.is_allowed(
            ACTOR,
            WORKSPACE,
            ACTION,
        )
        reports.append(
            DurableActionPermissionRevocationScenarioReport(
                scenario_id="authorization-remains-denied",
                status="denied" if denied else "allowed",
                passed=denied,
            )
        )

    return DurableActionPermissionRevocationDemoReport(
        phase="verify",
        scenarios=tuple(reports),
    )
