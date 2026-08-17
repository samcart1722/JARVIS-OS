"""Cross-process proof of durable actor-workspace membership admission."""

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import LIST_ITEMS_READ, PermissionGrant
from app.cognition.local_resolution.repository import InMemoryListItemRepository
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.cognition.trusted_context.models import (
    ConfiguredTrustedHostBinding,
    TrustedHostRequestInput,
    TrustedLocalCommandRequest,
)
from app.core.config import Settings
from app.core.container import Container
from app.infrastructure.local_storage import SQLiteLocalStorage

ACTIVE_ACTOR = ActorIdentity("durable-active")
INACTIVE_ACTOR = ActorIdentity("durable-inactive")
NON_MEMBER_ACTOR = ActorIdentity("durable-non-member")
NO_GRANT_ACTOR = ActorIdentity("durable-no-grant")
PRIMARY_WORKSPACE = WorkspaceIdentity("durable-primary")
ISOLATED_WORKSPACE = WorkspaceIdentity("durable-isolated")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class DurableMembershipScenarioReport:
    scenario_id: str
    status: str
    passed: bool
    membership_success: bool
    router_calls: int
    permission_calls: int
    repository_calls: int


@dataclass(frozen=True, slots=True)
class DurableMembershipDemoReport:
    phase: str
    scenarios: tuple[DurableMembershipScenarioReport, ...] = ()
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


def seed_durable_membership(database_path: Path) -> DurableMembershipDemoReport:
    with SQLiteLocalStorage(_require_external_database(database_path)) as storage:
        storage.initialize()
        storage.create(ACTIVE_ACTOR, PRIMARY_WORKSPACE)
        storage.create(INACTIVE_ACTOR, PRIMARY_WORKSPACE)
        storage.deactivate(INACTIVE_ACTOR, PRIMARY_WORKSPACE)
        storage.create(NO_GRANT_ACTOR, PRIMARY_WORKSPACE)
        if storage.get(NON_MEMBER_ACTOR, PRIMARY_WORKSPACE) is not None:
            raise RuntimeError("Durable membership seed failed.")
    return DurableMembershipDemoReport("seed")


def _request(binding: str, workspace: WorkspaceIdentity, text: str):
    return TrustedLocalCommandRequest(
        TrustedHostRequestInput(binding, workspace.workspace_id),
        text,
        CognitiveFallbackAuthorization(False),
    )


def _status(result) -> str:
    if not result.trust_resolution.success:
        return result.trust_resolution.error_code
    if not result.membership_decision.success:
        return result.membership_decision.error_code
    routed = result.text_routing_result
    if routed.interpretation.status.value == "invalid":
        return routed.interpretation.invalid_reason.value
    return routed.coordinated_result.local_result.error_code or "local_success"


def verify_durable_membership(database_path: Path) -> DurableMembershipDemoReport:
    bindings = tuple(
        ConfiguredTrustedHostBinding(
            f"binding-{actor.actor_id}",
            actor,
            frozenset(
                (PRIMARY_WORKSPACE.workspace_id, ISOLATED_WORKSPACE.workspace_id)
            ),
        )
        for actor in (ACTIVE_ACTOR, INACTIVE_ACTOR, NON_MEMBER_ACTOR, NO_GRANT_ACTOR)
    )
    repository = InMemoryListItemRepository()
    repository.add(PRIMARY_WORKSPACE, "demo-list", ("durable-item",))
    storage = SQLiteLocalStorage(_require_external_database(database_path))
    storage.open()
    storage.initialize()
    try:
        container = Container(
            Settings(REASONING_ENABLED=False, _env_file=None),
            membership_repository=storage,
            local_list_repository=repository,
            local_permission_grants=(
                PermissionGrant(
                    ACTIVE_ACTOR.actor_id,
                    PRIMARY_WORKSPACE.workspace_id,
                    frozenset((LIST_ITEMS_READ,)),
                ),
            ),
            trusted_host_bindings=bindings,
            trusted_known_workspaces=(PRIMARY_WORKSPACE, ISOLATED_WORKSPACE),
        )
        requests = (
            (
                "active-permitted",
                ACTIVE_ACTOR,
                PRIMARY_WORKSPACE,
                "list read demo-list",
            ),
            ("non-member", NON_MEMBER_ACTOR, PRIMARY_WORKSPACE, "list read demo-list"),
            (
                "inactive-member",
                INACTIVE_ACTOR,
                PRIMARY_WORKSPACE,
                "list read demo-list",
            ),
            (
                "active-no-grant",
                NO_GRANT_ACTOR,
                PRIMARY_WORKSPACE,
                "list read demo-list",
            ),
            (
                "workspace-isolation",
                ACTIVE_ACTOR,
                ISOLATED_WORKSPACE,
                "list read demo-list",
            ),
            (
                "payload-workspace-override",
                ACTIVE_ACTOR,
                PRIMARY_WORKSPACE,
                'knowledge store :: {"record_id":"record","kind":"fact",'
                '"key":"demo.key","value":"value","source_type":"user",'
                '"source_reference":"demo","workspace":"durable-isolated"}',
            ),
        )
        expected = (
            ("local_success", True, 1, 1, 1),
            ("membership_not_found", False, 0, 0, 0),
            ("membership_inactive", False, 0, 0, 0),
            ("local_permission_denied", True, 1, 1, 0),
            ("membership_not_found", False, 0, 0, 0),
            ("invalid_knowledge_fields", True, 1, 0, 0),
        )
        reports = []
        with ExitStack() as stack:
            router = stack.enter_context(
                patch.object(
                    container.local_command_text_router,
                    "route",
                    wraps=container.local_command_text_router.route,
                )
            )
            permission = stack.enter_context(
                patch.object(
                    container.local_permission_policy,
                    "is_allowed",
                    wraps=container.local_permission_policy.is_allowed,
                )
            )
            read = stack.enter_context(
                patch.object(repository, "read", wraps=repository.read)
            )
            model = stack.enter_context(
                patch.object(container.reasoning_provider, "generate")
            )
            provider = stack.enter_context(
                patch.object(container.ollama_client, "chat")
            )
            readiness = stack.enter_context(
                patch.object(container.provider_readiness_probe, "check")
            )
            network_get = stack.enter_context(patch("requests.get"))
            network_post = stack.enter_context(patch("requests.post"))
            for request, wanted in zip(requests, expected, strict=True):
                scenario_id, actor, workspace, text = request
                before = (router.call_count, permission.call_count, read.call_count)
                result = container.trusted_local_command_routing_service.route(
                    _request(f"binding-{actor.actor_id}", workspace, text)
                )
                deltas = tuple(
                    after - prior
                    for after, prior in zip(
                        (router.call_count, permission.call_count, read.call_count),
                        before,
                        strict=True,
                    )
                )
                status = _status(result)
                expected_status, member, *expected_deltas = wanted
                membership_success = bool(
                    result.membership_decision
                    and result.membership_decision.success
                )
                reports.append(
                    DurableMembershipScenarioReport(
                        scenario_id,
                        status,
                        status == expected_status
                        and membership_success is member
                        and list(deltas) == expected_deltas,
                        membership_success,
                        *deltas,
                    )
                )
        return DurableMembershipDemoReport(
            "verify",
            tuple(reports),
            model.call_count,
            provider.call_count,
            readiness.call_count,
            network_get.call_count + network_post.call_count,
        )
    finally:
        storage.close()
