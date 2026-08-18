"""Focused proofs for the internal trusted request-context demo runtime."""

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


def _run_demo():
    actor = ActorIdentity("actor-demo")
    primary = WorkspaceIdentity("workspace-primary")
    secondary = WorkspaceIdentity("workspace-secondary")
    unbound = WorkspaceIdentity("workspace-known-unbound")
    denied = WorkspaceIdentity("workspace-permission-denied")
    binding_selector = "configured-host-test-selector"
    binding = ConfiguredTrustedHostBinding(
        binding_selector,
        actor,
        frozenset((primary.workspace_id, secondary.workspace_id, denied.workspace_id)),
    )
    repository = InMemoryListItemRepository()
    repository.add(primary, "demo-list", ("item-alpha",))
    repository.add(secondary, "demo-list", ("item-beta",))
    grants = tuple(
        PermissionGrant(
            actor.actor_id, workspace.workspace_id, frozenset((LIST_ITEMS_READ,))
        )
        for workspace in (primary, secondary)
    )
    container = Container(
        Settings(REASONING_ENABLED=False, _env_file=None),
        memberships=tuple(
            ActorWorkspaceMembership(actor, workspace, MembershipStatus.ACTIVE)
            for workspace in (primary, secondary, denied)
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
                container.ollama_client, "chat", wraps=container.ollama_client.chat
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
    return (
        report,
        repository,
        primary,
        secondary,
        model,
        provider,
        readiness,
        network_get,
        network_post,
    )


def test_all_seven_scenarios_have_expected_results_and_boundaries() -> None:
    report, repository, primary, secondary, *remote = _run_demo()
    assert report.success
    assert tuple(scenario.scenario_id for scenario in report.scenarios) == (
        "valid-permitted",
        "unknown-binding",
        "unknown-workspace",
        "known-unbound-workspace",
        "explicit-second-workspace",
        "downstream-permission-denial",
        "payload-workspace-override",
    )
    assert tuple(scenario.status for scenario in report.scenarios) == (
        "local_success",
        "trusted_context_unknown_binding",
        "trusted_context_unknown_workspace",
        "trusted_context_workspace_not_bound",
        "local_success",
        "local_permission_denied",
        "invalid_knowledge_fields",
    )
    assert tuple(scenario.router_calls for scenario in report.scenarios) == (
        1,
        0,
        0,
        0,
        1,
        1,
        1,
    )
    assert tuple(scenario.cognitive_calls for scenario in report.scenarios) == (0,) * 7
    assert report.scenarios[4].items == ("item-beta",)
    assert "item-alpha" not in report.scenarios[4].items
    assert report.scenarios[5].trust_success
    assert report.scenarios[5].permission_calls == 1
    assert report.scenarios[6].trust_success
    assert report.scenarios[6].repository_calls == 0
    assert repository.read(primary, "demo-list").items == ("item-alpha",)
    assert repository.read(secondary, "demo-list").items == ("item-beta",)
    assert all(
        value == 0
        for value in (
            report.model_calls,
            report.provider_calls,
            report.readiness_calls,
            report.network_calls,
        )
    )
    for observer in remote:
        observer.assert_not_called()


def test_trust_failures_short_circuit_before_downstream_boundaries() -> None:
    report, *_ = _run_demo()
    for scenario in report.scenarios[1:4]:
        assert not scenario.trust_success
        assert scenario.router_calls == 0
        assert scenario.permission_calls == 0
        assert scenario.repository_calls == 0
        assert scenario.cognitive_calls == 0
