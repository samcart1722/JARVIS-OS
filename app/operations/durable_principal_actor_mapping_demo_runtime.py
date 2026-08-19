"""Cross-process proof of durable principal-to-actor mapping."""

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, patch

from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import LIST_ITEMS_READ, PermissionGrant
from app.cognition.local_resolution.repository import InMemoryListItemRepository
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.core.config import Settings
from app.core.container import Container
from app.infrastructure.local_storage import (
    SQLiteLocalStorage,
    SQLitePrincipalActorMappingRepository,
)
from app.principal_authentication import (
    AuthenticatedLocalCommandRequest,
    ConfiguredPrincipalProofBinding,
    LocalAuthenticationProof,
    PrincipalActorMappingConflict,
    PrincipalIdentity,
)

PRIMARY_PRINCIPAL = PrincipalIdentity("Durable-Principal")
SECONDARY_PRINCIPAL = PrincipalIdentity("Durable-Principal-Secondary")
CASE_VARIANT_PRINCIPAL = PrincipalIdentity("durable-principal")
ACTOR = ActorIdentity("durable-principal-actor")
WORKSPACE = WorkspaceIdentity("durable-principal-workspace")

PRIMARY_PROOF = "durable-proof-primary"
SECONDARY_PROOF = "durable-proof-secondary"
CASE_VARIANT_PROOF = "durable-proof-case-variant"

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class DurablePrincipalActorScenarioReport:
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
    permission_calls: int = 0
    capability_repository_calls: int = 0
    cognitive_calls: int = 0


@dataclass(frozen=True, slots=True)
class DurablePrincipalActorMappingDemoReport:
    phase: str
    scenarios: tuple[DurablePrincipalActorScenarioReport, ...]
    model_calls: int = 0
    provider_calls: int = 0
    readiness_calls: int = 0
    network_calls: int = 0

    @property
    def success(self) -> bool:
        return all(scenario.passed for scenario in self.scenarios) and not any(
            (
                self.model_calls,
                self.provider_calls,
                self.readiness_calls,
                self.network_calls,
            )
        )


def _require_external_database(database_path: Path) -> Path:
    path = database_path.resolve()
    if path == REPOSITORY_ROOT or REPOSITORY_ROOT in path.parents:
        raise ValueError("Demo database must be outside the repository.")
    return path


def seed_durable_principal_actor_mapping(
    database_path: Path,
) -> DurablePrincipalActorMappingDemoReport:
    reports = []

    with SQLiteLocalStorage(
        _require_external_database(database_path)
    ) as storage:
        storage.initialize()
        repository = SQLitePrincipalActorMappingRepository(storage)

        created = repository.create(PRIMARY_PRINCIPAL, ACTOR)
        reports.append(
            DurablePrincipalActorScenarioReport(
                "primary-mapping-created",
                "created",
                created == ACTOR
                and repository.get(PRIMARY_PRINCIPAL) == ACTOR,
            )
        )

        conflict_passed = False
        try:
            repository.create(
                PRIMARY_PRINCIPAL,
                ActorIdentity("forbidden-overwrite"),
            )
        except PrincipalActorMappingConflict:
            conflict_passed = repository.get(PRIMARY_PRINCIPAL) == ACTOR

        reports.append(
            DurablePrincipalActorScenarioReport(
                "duplicate-principal-rejected",
                "conflict_rejected",
                conflict_passed,
            )
        )

        secondary = repository.create(SECONDARY_PRINCIPAL, ACTOR)
        shared_passed = (
            secondary == ACTOR
            and repository.get(PRIMARY_PRINCIPAL) == ACTOR
            and repository.get(SECONDARY_PRINCIPAL) == ACTOR
            and repository.get(CASE_VARIANT_PRINCIPAL) is None
        )

        reports.append(
            DurablePrincipalActorScenarioReport(
                "multiple-principals-share-actor",
                "shared_actor",
                shared_passed,
            )
        )

    return DurablePrincipalActorMappingDemoReport(
        "seed",
        tuple(reports),
    )


def _status(result) -> str:
    if not result.authentication_result.success:
        return result.authentication_result.error_code.value

    if not result.mapping_result.success:
        return result.mapping_result.error_code.value

    if not result.workspace_selection_result.success:
        return result.workspace_selection_result.error_code.value

    if not result.membership_decision.success:
        return result.membership_decision.error_code.value

    routed = result.text_routing_result

    if (
        routed.interpretation.status
        is LocalCommandInterpretationStatus.INVALID
    ):
        return routed.interpretation.invalid_reason.value

    return (
        routed.coordinated_result.local_result.error_code
        or "local_success"
    )


def _request(proof: object) -> AuthenticatedLocalCommandRequest:
    return AuthenticatedLocalCommandRequest(
        LocalAuthenticationProof(proof),
        WORKSPACE.workspace_id,
        "list read demo-list",
        CognitiveFallbackAuthorization(False),
    )


def verify_durable_principal_actor_mapping(
    database_path: Path,
) -> DurablePrincipalActorMappingDemoReport:
    storage = SQLiteLocalStorage(
        _require_external_database(database_path)
    )
    storage.open()
    storage.initialize()

    try:
        mapping_repository = (
            SQLitePrincipalActorMappingRepository(storage)
        )

        if mapping_repository.get(PRIMARY_PRINCIPAL) != ACTOR:
            raise RuntimeError(
                "Primary durable mapping was not recovered."
            )

        if mapping_repository.get(SECONDARY_PRINCIPAL) != ACTOR:
            raise RuntimeError(
                "Secondary durable mapping was not recovered."
            )

        if mapping_repository.get(CASE_VARIANT_PRINCIPAL) is not None:
            raise RuntimeError(
                "Case-sensitive mapping boundary was not preserved."
            )

        storage.create(ACTOR, WORKSPACE)

        list_repository = InMemoryListItemRepository()
        list_repository.add(
            WORKSPACE,
            "demo-list",
            ("durable-item",),
        )

        container = Container(
            Settings(
                REASONING_ENABLED=False,
                _env_file=None,
            ),
            membership_repository=storage,
            local_list_repository=list_repository,
            local_permission_grants=(
                PermissionGrant(
                    ACTOR.actor_id,
                    WORKSPACE.workspace_id,
                    frozenset((LIST_ITEMS_READ,)),
                ),
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
                ConfiguredPrincipalProofBinding(
                    CASE_VARIANT_PRINCIPAL,
                    CASE_VARIANT_PROOF,
                ),
            ),
            principal_actor_mapping_repository=(
                mapping_repository
            ),
        )

        service = (
            container.authenticated_local_command_routing_service
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

        requests = (
            (
                "primary-durable-routing",
                PRIMARY_PROOF,
                "local_success",
                True,
                True,
                True,
                (1, 1, 1, 1, 1, 1, 1, 0),
            ),
            (
                "secondary-shared-actor-routing",
                SECONDARY_PROOF,
                "local_success",
                True,
                True,
                True,
                (1, 1, 1, 1, 1, 1, 1, 0),
            ),
            (
                "case-sensitive-mapping-miss",
                CASE_VARIANT_PROOF,
                "principal_mapping_failed",
                True,
                False,
                False,
                (1, 1, 1, 0, 0, 0, 0, 0),
            ),
        )

        reports = []

        with ExitStack() as stack:
            mapping_get = stack.enter_context(
                patch.object(
                    mapping_repository,
                    "get",
                    wraps=mapping_repository.get,
                )
            )

            permission = stack.enter_context(
                patch.object(
                    container.local_permission_policy,
                    "is_allowed",
                    wraps=(
                        container.local_permission_policy.is_allowed
                    ),
                )
            )

            list_read = stack.enter_context(
                patch.object(
                    list_repository,
                    "read",
                    wraps=list_repository.read,
                )
            )

            cognitive = stack.enter_context(
                patch.object(
                    container.cognitive_engine,
                    "process",
                    wraps=container.cognitive_engine.process,
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
                patch("requests.get")
            )
            network_post = stack.enter_context(
                patch("requests.post")
            )

            for (
                scenario_id,
                proof,
                expected_status,
                expected_authentication,
                expected_mapping,
                expected_membership,
                expected_deltas,
            ) in requests:
                before = (
                    authenticator.authenticate.call_count,
                    mapper.map.call_count,
                    mapping_get.call_count,
                    membership.decide.call_count,
                    router.route.call_count,
                    permission.call_count,
                    list_read.call_count,
                    cognitive.call_count,
                )

                result = service.route(
                    _request(proof)
                )

                after = (
                    authenticator.authenticate.call_count,
                    mapper.map.call_count,
                    mapping_get.call_count,
                    membership.decide.call_count,
                    router.route.call_count,
                    permission.call_count,
                    list_read.call_count,
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

                reports.append(
                    DurablePrincipalActorScenarioReport(
                        scenario_id=scenario_id,
                        status=status,
                        passed=(
                            status == expected_status
                            and authentication_success
                            is expected_authentication
                            and mapping_success
                            is expected_mapping
                            and membership_success
                            is expected_membership
                            and deltas == expected_deltas
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
                        permission_calls=deltas[5],
                        capability_repository_calls=deltas[6],
                        cognitive_calls=deltas[7],
                    )
                )

        return DurablePrincipalActorMappingDemoReport(
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
