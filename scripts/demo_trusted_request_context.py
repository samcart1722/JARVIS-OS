"""Thin composition adapter for the internal trusted request-context demo."""

from contextlib import ExitStack
from unittest.mock import patch

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import LIST_ITEMS_READ, PermissionGrant
from app.cognition.local_resolution.repository import InMemoryListItemRepository
from app.cognition.trusted_context.models import ConfiguredTrustedHostBinding
from app.core.config import Settings
from app.core.container import Container
from app.membership.models import ActorWorkspaceMembership, MembershipStatus
from app.operations.trusted_request_context_demo_runtime import (
    TrustedRequestContextDemoRuntime,
)


def main() -> int:
    title = "Luxiom Internal Trusted Request-Context Demo v1"
    try:
        actor = ActorIdentity("actor-demo")
        primary = WorkspaceIdentity("workspace-primary")
        secondary = WorkspaceIdentity("workspace-secondary")
        unbound = WorkspaceIdentity("workspace-known-unbound")
        denied = WorkspaceIdentity("workspace-permission-denied")
        binding_selector = "configured-host-demo-selector"
        binding = ConfiguredTrustedHostBinding(
            binding_selector,
            actor,
            frozenset(
                (primary.workspace_id, secondary.workspace_id, denied.workspace_id)
            ),
        )
        repository = InMemoryListItemRepository()
        repository.add(primary, "demo-list", ("item-alpha",))
        repository.add(secondary, "demo-list", ("item-beta",))
        grants = (
            PermissionGrant(
                actor.actor_id,
                primary.workspace_id,
                frozenset((LIST_ITEMS_READ,)),
            ),
            PermissionGrant(
                actor.actor_id,
                secondary.workspace_id,
                frozenset((LIST_ITEMS_READ,)),
            ),
        )
        container = Container(
            Settings(REASONING_ENABLED=False, _env_file=None),
            memberships=(
                ActorWorkspaceMembership(actor, primary, MembershipStatus.ACTIVE),
                ActorWorkspaceMembership(actor, secondary, MembershipStatus.ACTIVE),
                ActorWorkspaceMembership(actor, denied, MembershipStatus.ACTIVE),
            ),
            local_permission_grants=grants,
            local_list_repository=repository,
            trusted_host_bindings=(binding,),
            trusted_known_workspaces=(primary, secondary, unbound, denied),
        )
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
            report = TrustedRequestContextDemoRuntime(
                container.trusted_local_command_routing_service,
                binding_selector,
                primary.workspace_id,
                secondary.workspace_id,
                unbound.workspace_id,
                denied.workspace_id,
                router,
                permission,
                (list_read, knowledge_store),
                cognitive,
                (model,),
                (provider,),
                (readiness,),
                (network_get, network_post),
            ).run()
        print(title)
        for scenario in report.scenarios:
            print(f"Scenario: {scenario.scenario_id}")
            print(f"Status: {'PASS' if scenario.passed else 'FAIL'}")
            print(f"Result: {scenario.status}")
            print(f"Router calls: {scenario.router_calls}")
        print(f"Model calls: {report.model_calls}")
        print(f"Provider calls: {report.provider_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        print(f"Overall: {'PASS' if report.success else 'FAIL'}")
        return 0 if report.success else 1
    except Exception:
        print(title)
        print("Trusted request-context demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
