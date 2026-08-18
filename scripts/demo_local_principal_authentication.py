"""Thin composition adapter for the internal local-principal auth demo."""

from contextlib import ExitStack
from unittest.mock import Mock, patch

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import LIST_ITEMS_READ, PermissionGrant
from app.cognition.local_resolution.repository import InMemoryListItemRepository
from app.core.config import Settings
from app.core.container import Container
from app.membership.models import ActorWorkspaceMembership, MembershipStatus
from app.operations.local_principal_authentication_demo_runtime import (
    LocalPrincipalAuthenticationDemoRuntime,
)
from app.principal_authentication import (
    AuthenticatedLocalCommandRoutingService,
    ConfiguredPrincipalActorMapping,
    ConfiguredPrincipalProofBinding,
    PrincipalIdentity,
)


def _build_report():
    actor = ActorIdentity("actor-demo")
    mapped_principal = PrincipalIdentity("principal-demo-mapped")
    unmapped_principal = PrincipalIdentity("principal-demo-unmapped")
    primary = WorkspaceIdentity("workspace-primary")
    absent = WorkspaceIdentity("workspace-membership-absent")
    inactive = WorkspaceIdentity("workspace-membership-inactive")
    denied = WorkspaceIdentity("workspace-permission-denied")
    valid_proof = "internal-demo-proof-mapped"
    unmapped_proof = "internal-demo-proof-unmapped"
    repository = InMemoryListItemRepository()
    repository.add(primary, "demo-list", ("item-alpha",))
    container = Container(
        Settings(REASONING_ENABLED=False, _env_file=None),
        memberships=(
            ActorWorkspaceMembership(actor, primary, MembershipStatus.ACTIVE),
            ActorWorkspaceMembership(actor, inactive, MembershipStatus.INACTIVE),
            ActorWorkspaceMembership(actor, denied, MembershipStatus.ACTIVE),
        ),
        local_permission_grants=(
            PermissionGrant(
                actor.actor_id,
                primary.workspace_id,
                frozenset((LIST_ITEMS_READ,)),
            ),
        ),
        local_list_repository=repository,
        principal_proof_bindings=(
            ConfiguredPrincipalProofBinding(mapped_principal, valid_proof),
            ConfiguredPrincipalProofBinding(unmapped_principal, unmapped_proof),
        ),
        principal_actor_mappings=(
            ConfiguredPrincipalActorMapping(mapped_principal, actor),
        ),
    )
    authenticator = Mock(wraps=container.local_principal_authenticator)
    mapper = Mock(wraps=container.principal_actor_mapper)
    membership = Mock(wraps=container.membership_decision_service)
    router = Mock(wraps=container.local_command_text_router)
    service = AuthenticatedLocalCommandRoutingService(
        authenticator,
        mapper,
        membership,
        router,
    )
    with ExitStack() as stack:
        permission = stack.enter_context(
            patch.object(
                container.local_permission_policy,
                "is_allowed",
                wraps=container.local_permission_policy.is_allowed,
            )
        )
        list_read = stack.enter_context(
            patch.object(repository, "read", wraps=repository.read)
        )
        knowledge_store = stack.enter_context(
            patch.object(
                container.local_knowledge_repository,
                "store",
                wraps=container.local_knowledge_repository.store,
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
                wraps=container.reasoning_provider.generate,
            )
        )
        provider = stack.enter_context(
            patch.object(
                container.ollama_client,
                "chat",
                wraps=container.ollama_client.chat,
            )
        )
        readiness = stack.enter_context(
            patch.object(
                container.provider_readiness_probe,
                "check",
                wraps=container.provider_readiness_probe.check,
            )
        )
        network_get = stack.enter_context(patch("requests.get"))
        network_post = stack.enter_context(patch("requests.post"))
        return LocalPrincipalAuthenticationDemoRuntime(
            service,
            valid_proof,
            unmapped_proof,
            primary.workspace_id,
            absent.workspace_id,
            inactive.workspace_id,
            denied.workspace_id,
            authenticator.authenticate,
            mapper.map,
            membership.decide,
            router.route,
            permission,
            (list_read, knowledge_store),
            cognitive,
            (model,),
            (provider,),
            (readiness,),
            (network_get, network_post),
        ).run()


def main() -> int:
    title = "Luxiom Internal Local Principal Authentication Demo v1"
    try:
        report = _build_report()
        print(title)
        for scenario in report.scenarios:
            print(f"Scenario: {scenario.scenario_id}")
            print(f"Status: {'PASS' if scenario.passed else 'FAIL'}")
            print(f"Result: {scenario.status}")
            print(
                "Calls: "
                f"auth={scenario.authenticator_calls}, "
                f"map={scenario.mapper_calls}, "
                f"membership={scenario.membership_calls}, "
                f"router={scenario.router_calls}, "
                f"permission={scenario.permission_calls}, "
                f"repository={scenario.repository_calls}, "
                f"cognitive={scenario.cognitive_calls}"
            )
        print(f"Model calls: {report.model_calls}")
        print(f"Provider calls: {report.provider_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        print(f"Overall: {'PASS' if report.success else 'FAIL'}")
        return 0 if report.success else 1
    except Exception:
        print(title)
        print("Local principal authentication demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
