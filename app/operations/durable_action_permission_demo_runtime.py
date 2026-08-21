"""Cross-process proof of durable local action permissions."""

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, patch

from app.cognition.interpretation.models import (
    LocalCommandInterpretationStatus,
)
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
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
)
from app.core.config import Settings
from app.core.container import Container
from app.infrastructure.local_storage import (
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
    SQLitePrincipalActorMappingRepository,
)
from app.membership import MembershipStatus
from app.principal_authentication import (
    AuthenticatedLocalCommandRequest,
    ConfiguredPrincipalProofBinding,
    LocalAuthenticationProof,
    PrincipalIdentity,
)

PRIMARY_PRINCIPAL = PrincipalIdentity(
    "Durable-Permission-Principal"
)

SECONDARY_PRINCIPAL = PrincipalIdentity(
    "Durable-Permission-Secondary"
)

ACTOR = ActorIdentity(
    "durable-permission-actor"
)

OTHER_ACTOR = ActorIdentity(
    "durable-permission-other-actor"
)

WORKSPACE = WorkspaceIdentity(
    "durable-permission-workspace"
)

OTHER_WORKSPACE = WorkspaceIdentity(
    "durable-permission-other-workspace"
)

PRIMARY_PROOF = "durable-permission-proof"
SECONDARY_PROOF = "durable-permission-secondary-proof"

LIST_ID = "demo-list"
LIST_ITEM = "durable-permission-item"

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class DurableActionPermissionScenarioReport:
    scenario_id: str
    status: str
    passed: bool
    authentication_success: bool = False
    mapping_success: bool = False
    membership_success: bool = False
    authenticator_calls: int = 0
    mapper_calls: int = 0
    mapping_repository_calls: int = 0
    membership_calls: int = 0
    router_calls: int = 0
    permission_repository_calls: int = 0
    list_read_calls: int = 0
    list_add_calls: int = 0
    cognitive_calls: int = 0


@dataclass(frozen=True, slots=True)
class DurableActionPermissionDemoReport:
    phase: str
    scenarios: tuple[
        DurableActionPermissionScenarioReport,
        ...
    ]
    model_calls: int = 0
    provider_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    @property
    def success(self) -> bool:
        return (
            all(
                scenario.passed
                for scenario in self.scenarios
            )
            and not any(
                (
                    self.model_calls,
                    self.provider_calls,
                    self.readiness_calls,
                    self.network_calls,
                )
            )
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


def seed_durable_action_permission(
    database_path: Path,
) -> DurableActionPermissionDemoReport:
    reports = []

    with SQLiteLocalStorage(
        _require_external_database(database_path)
    ) as storage:
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

        mapping_repository.create(
            PRIMARY_PRINCIPAL,
            ACTOR,
        )

        mapping_repository.create(
            SECONDARY_PRINCIPAL,
            OTHER_ACTOR,
        )

        primary_membership = storage.create(
            ACTOR,
            WORKSPACE,
        )

        alternate_workspace_membership = storage.create(
            ACTOR,
            OTHER_WORKSPACE,
        )

        alternate_actor_membership = storage.create(
            OTHER_ACTOR,
            WORKSPACE,
        )

        identity_membership_passed = (
            mapping_repository.get(
                PRIMARY_PRINCIPAL
            )
            == ACTOR
            and mapping_repository.get(
                SECONDARY_PRINCIPAL
            )
            == OTHER_ACTOR
            and primary_membership.status
            is MembershipStatus.ACTIVE
            and alternate_workspace_membership.status
            is MembershipStatus.ACTIVE
            and alternate_actor_membership.status
            is MembershipStatus.ACTIVE
        )

        reports.append(
            DurableActionPermissionScenarioReport(
                scenario_id=(
                    "durable-identity-membership-seeded"
                ),
                status="seeded",
                passed=identity_membership_passed,
            )
        )

        permission_repository.create(
            ACTOR,
            WORKSPACE,
            LIST_ITEMS_READ,
        )

        reports.append(
            DurableActionPermissionScenarioReport(
                scenario_id="exact-permission-created",
                status="created",
                passed=permission_repository.is_granted(
                    ACTOR,
                    WORKSPACE,
                    LIST_ITEMS_READ,
                ),
            )
        )

        duplicate_rejected = False

        try:
            permission_repository.create(
                ACTOR,
                WORKSPACE,
                LIST_ITEMS_READ,
            )
        except PermissionGrantConflict:
            duplicate_rejected = (
                permission_repository.is_granted(
                    ACTOR,
                    WORKSPACE,
                    LIST_ITEMS_READ,
                )
            )

        reports.append(
            DurableActionPermissionScenarioReport(
                scenario_id=(
                    "duplicate-permission-rejected"
                ),
                status="conflict_rejected",
                passed=duplicate_rejected,
            )
        )

        exact_boundary_passed = (
            not permission_repository.is_granted(
                ActorIdentity(
                    "Durable-Permission-Actor"
                ),
                WORKSPACE,
                LIST_ITEMS_READ,
            )
            and not permission_repository.is_granted(
                ACTOR,
                WorkspaceIdentity(
                    "Durable-Permission-Workspace"
                ),
                LIST_ITEMS_READ,
            )
            and not permission_repository.is_granted(
                ACTOR,
                WORKSPACE,
                "LIST.ITEMS.READ",
            )
            and not permission_repository.is_granted(
                ACTOR,
                WORKSPACE,
                LIST_ITEMS_ADD,
            )
        )

        reports.append(
            DurableActionPermissionScenarioReport(
                scenario_id=(
                    "permission-boundary-is-exact"
                ),
                status="exact",
                passed=exact_boundary_passed,
            )
        )

        storage.add(
            WORKSPACE,
            LIST_ID,
            (
                LIST_ITEM,
            ),
        )

        reports.append(
            DurableActionPermissionScenarioReport(
                scenario_id="durable-list-seeded",
                status="seeded",
                passed=(
                    storage.read(
                        WORKSPACE,
                        LIST_ID,
                    ).items
                    == (
                        LIST_ITEM,
                    )
                ),
            )
        )

    return DurableActionPermissionDemoReport(
        phase="seed",
        scenarios=tuple(reports),
    )


def _status(result) -> str:
    if not result.authentication_result.success:
        return (
            result.authentication_result
            .error_code.value
        )

    if not result.mapping_result.success:
        return result.mapping_result.error_code.value

    if not result.workspace_selection_result.success:
        return (
            result.workspace_selection_result
            .error_code.value
        )

    if not result.membership_decision.success:
        return (
            result.membership_decision
            .error_code.value
        )

    routed = result.text_routing_result

    if routed is None:
        return "routing_missing"

    if (
        routed.interpretation.status
        is LocalCommandInterpretationStatus.INVALID
    ):
        return routed.interpretation.invalid_reason.value

    return (
        routed.coordinated_result
        .local_result.error_code
        or "local_success"
    )


def _request(
    proof: object,
    workspace: WorkspaceIdentity,
    text: str,
) -> AuthenticatedLocalCommandRequest:
    return AuthenticatedLocalCommandRequest(
        LocalAuthenticationProof(proof),
        workspace.workspace_id,
        text,
        CognitiveFallbackAuthorization(False),
    )


def verify_durable_action_permission(
    database_path: Path,
) -> DurableActionPermissionDemoReport:
    storage = SQLiteLocalStorage(
        _require_external_database(database_path)
    )

    storage.open()
    storage.initialize()

    try:
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

        if (
            mapping_repository.get(
                PRIMARY_PRINCIPAL
            )
            != ACTOR
        ):
            raise RuntimeError(
                "Primary durable mapping was not recovered."
            )

        if (
            mapping_repository.get(
                SECONDARY_PRINCIPAL
            )
            != OTHER_ACTOR
        ):
            raise RuntimeError(
                "Secondary durable mapping was not recovered."
            )

        required_memberships = (
            (
                ACTOR,
                WORKSPACE,
            ),
            (
                ACTOR,
                OTHER_WORKSPACE,
            ),
            (
                OTHER_ACTOR,
                WORKSPACE,
            ),
        )

        for actor, workspace in required_memberships:
            membership = storage.get(
                actor,
                workspace,
            )

            if (
                membership is None
                or membership.status
                is not MembershipStatus.ACTIVE
            ):
                raise RuntimeError(
                    "Required durable membership "
                    "was not recovered."
                )

        if not permission_repository.is_granted(
            ACTOR,
            WORKSPACE,
            LIST_ITEMS_READ,
        ):
            raise RuntimeError(
                "Durable permission was not recovered."
            )

        if permission_repository.is_granted(
            ACTOR,
            WORKSPACE,
            "LIST.ITEMS.READ",
        ):
            raise RuntimeError(
                "Permission case boundary was not preserved."
            )

        if (
            storage.read(
                WORKSPACE,
                LIST_ID,
            ).items
            != (
                LIST_ITEM,
            )
        ):
            raise RuntimeError(
                "Durable list state was not recovered."
            )

        mapping_runtime = Mock(
            wraps=mapping_repository
        )

        permission_runtime = Mock(
            wraps=permission_repository
        )

        container = Container(
            Settings(
                REASONING_ENABLED=False,
                _env_file=None,
            ),
            local_list_repository=storage,
            membership_repository=storage,
            local_permission_grant_repository=(
                permission_runtime
            ),
            principal_proof_bindings=(
                ConfiguredPrincipalProofBinding(
                    PRIMARY_PRINCIPAL,
                    PRIMARY_PROOF,
                ),
                ConfiguredPrincipalProofBinding(
                    SECONDARY_PRINCIPAL,
                    SECONDARY_PROOF,
                ),
            ),
            principal_actor_mapping_repository=(
                mapping_runtime
            ),
        )

        service = (
            container
            .authenticated_local_command_routing_service
        )

        authenticator = Mock(
            wraps=container.local_principal_authenticator
        )

        mapper = Mock(
            wraps=container.principal_actor_mapper
        )

        membership = Mock(
            wraps=container.membership_decision_service
        )

        router = Mock(
            wraps=container.local_command_text_router
        )

        service._authenticator = authenticator
        service._mapper = mapper
        service._membership_service = membership
        service._router = router

        scenarios = (
            (
                "exact-durable-permission-success",
                PRIMARY_PROOF,
                WORKSPACE,
                f"list read {LIST_ID}",
                "local_success",
                (
                    LIST_ITEM,
                ),
                False,
                (
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                ),
            ),
            (
                "wrong-workspace-denied",
                PRIMARY_PROOF,
                OTHER_WORKSPACE,
                f"list read {LIST_ID}",
                "local_permission_denied",
                None,
                False,
                (
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                    0,
                ),
            ),
            (
                "wrong-action-denied",
                PRIMARY_PROOF,
                WORKSPACE,
                (
                    f"list add {LIST_ID} "
                    ":: blocked-item"
                ),
                "local_permission_denied",
                None,
                False,
                (
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                    0,
                ),
            ),
            (
                "wrong-actor-denied",
                SECONDARY_PROOF,
                WORKSPACE,
                f"list read {LIST_ID}",
                "local_permission_denied",
                None,
                False,
                (
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                    0,
                ),
            ),
            (
                "permission-repository-failure-denied",
                PRIMARY_PROOF,
                WORKSPACE,
                f"list read {LIST_ID}",
                "local_permission_denied",
                None,
                True,
                (
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    0,
                    0,
                    0,
                ),
            ),
        )

        reports = []

        with ExitStack() as stack:
            membership_get = stack.enter_context(
                patch.object(
                    storage,
                    "get",
                    wraps=storage.get,
                )
            )

            list_read = stack.enter_context(
                patch.object(
                    storage,
                    "read",
                    wraps=storage.read,
                )
            )

            list_add = stack.enter_context(
                patch.object(
                    storage,
                    "add",
                    wraps=storage.add,
                )
            )

            cognitive = stack.enter_context(
                patch.object(
                    container.cognitive_engine,
                    "process",
                    wraps=(
                        container.cognitive_engine.process
                    ),
                )
            )

            model = stack.enter_context(
                patch.object(
                    container.reasoning_provider,
                    "generate",
                )
            )

            provider = stack.enter_context(
                patch.object(
                    container.ollama_client,
                    "chat",
                )
            )

            readiness = stack.enter_context(
                patch.object(
                    container.provider_readiness_probe,
                    "check",
                )
            )

            network_get = stack.enter_context(
                patch(
                    "requests.get"
                )
            )

            network_post = stack.enter_context(
                patch(
                    "requests.post"
                )
            )

            for (
                scenario_id,
                proof,
                workspace,
                text,
                expected_status,
                expected_items,
                fail_permission_repository,
                expected_deltas,
            ) in scenarios:
                before = (
                    authenticator.authenticate.call_count,
                    mapper.map.call_count,
                    mapping_runtime.get.call_count,
                    membership_get.call_count,
                    router.route.call_count,
                    permission_runtime.is_granted.call_count,
                    list_read.call_count,
                    list_add.call_count,
                    cognitive.call_count,
                )

                if fail_permission_repository:
                    permission_runtime.is_granted.side_effect = (
                        PermissionGrantRepositoryError(
                            "simulated permission "
                            "repository failure"
                        )
                    )

                try:
                    result = service.route(
                        _request(
                            proof,
                            workspace,
                            text,
                        )
                    )
                finally:
                    permission_runtime.is_granted.side_effect = (
                        None
                    )

                after = (
                    authenticator.authenticate.call_count,
                    mapper.map.call_count,
                    mapping_runtime.get.call_count,
                    membership_get.call_count,
                    router.route.call_count,
                    permission_runtime.is_granted.call_count,
                    list_read.call_count,
                    list_add.call_count,
                    cognitive.call_count,
                )

                deltas = tuple(
                    end - start
                    for start, end in zip(
                        before,
                        after,
                        strict=True,
                    )
                )

                status = _status(result)

                authentication_success = (
                    result.authentication_result.success
                )

                mapping_success = bool(
                    result.mapping_result
                    and result.mapping_result.success
                )

                membership_success = bool(
                    result.membership_decision
                    and result.membership_decision.success
                )

                payload_ok = True

                if expected_items is not None:
                    payload_ok = (
                        result.text_routing_result
                        .coordinated_result
                        .local_result.items
                        == expected_items
                    )

                reports.append(
                    DurableActionPermissionScenarioReport(
                        scenario_id=scenario_id,
                        status=status,
                        passed=(
                            status == expected_status
                            and authentication_success
                            and mapping_success
                            and membership_success
                            and payload_ok
                            and deltas
                            == expected_deltas
                        ),
                        authentication_success=(
                            authentication_success
                        ),
                        mapping_success=mapping_success,
                        membership_success=(
                            membership_success
                        ),
                        authenticator_calls=deltas[0],
                        mapper_calls=deltas[1],
                        mapping_repository_calls=deltas[2],
                        membership_calls=deltas[3],
                        router_calls=deltas[4],
                        permission_repository_calls=(
                            deltas[5]
                        ),
                        list_read_calls=deltas[6],
                        list_add_calls=deltas[7],
                        cognitive_calls=deltas[8],
                    )
                )

        return DurableActionPermissionDemoReport(
            phase="verify",
            scenarios=tuple(reports),
            model_calls=model.call_count,
            provider_calls=provider.call_count,
            readiness_calls=readiness.call_count,
            network_calls=(
                network_get.call_count
                + network_post.call_count
            ),
        )

    finally:
        storage.close()
