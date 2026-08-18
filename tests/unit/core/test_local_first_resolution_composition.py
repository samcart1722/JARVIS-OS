from unittest.mock import Mock, patch

import pytest

from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    FindKnowledgeRecordsQuery,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_READ,
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    PermissionGrant,
)
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.cognition.trusted_context import (
    TRUSTED_CONTEXT_RESOLUTION_FAILED,
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    ConfiguredTrustedHostBinding,
    ConfiguredTrustedRequestContextResolver,
    TrustedHostRequestInput,
    TrustedLocalCommandRequest,
    TrustedRequestContextResolution,
)
from app.core.config import Settings
from app.core.container import Container
from app.infrastructure.local_storage import SQLiteLocalStorage
from app.membership import (
    ActorWorkspaceMembership,
    InMemoryMembershipRepository,
    MembershipDecisionService,
    MembershipStatus,
)


class FalseyRepository:
    def __bool__(self) -> bool:
        return False

    def get(self, actor, workspace):
        return None


def test_container_composes_one_shared_local_repository_without_calls() -> None:
    grant = PermissionGrant("a", "w", frozenset((LIST_ITEMS_ADD, LIST_ITEMS_READ)))
    with (
        patch("app.models.ollama_client.OllamaClient.chat") as chat,
        patch("app.models.ollama_readiness_probe.OllamaReadinessProbe.check") as ready,
        patch("requests.get") as network_get,
        patch("requests.post") as network_post,
    ):
        container = Container(
            Settings(_env_file=None), local_permission_grants=(grant,)
        )
        actor, workspace = ActorIdentity("a"), WorkspaceIdentity("w")
        add = container.local_first_resolver.resolve(
            actor, workspace, AddListItemsCommand("l", ("x", "x"))
        )
        read = container.local_first_resolver.resolve(
            actor, workspace, ReadListItemsQuery("l")
        )
        denied = container.local_first_resolver.resolve(
            ActorIdentity("denied"), workspace, ReadListItemsQuery("l")
        )
        invalid = container.local_first_resolver.resolve(
            None, workspace, ReadListItemsQuery("l")
        )
        unsupported = container.local_first_resolver.resolve(actor, workspace, object())
    assert add.already_present == ("x",) and read.items == ("x",)
    assert not denied.success and invalid.error_code == "local_validation_failed"
    assert not unsupported.handled
    assert (
        container.structured_list_capability._repository
        is container.local_list_repository
    )
    chat.assert_not_called()
    ready.assert_not_called()
    network_get.assert_not_called()
    network_post.assert_not_called()


def test_existing_reasoning_path_remains_separate_and_calls_provider_once() -> None:
    container = Container(Settings(REASONING_ENABLED=True, _env_file=None))
    with patch.object(container.reasoning_provider, "generate") as generate:
        generate.return_value = ReasoningResult(response="ok")
        container.cognitive_engine.process("unrelated reasoning request")
    generate.assert_called_once()


def test_default_container_construction_creates_no_database(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    Container(Settings(_env_file=None))
    assert tuple(tmp_path.iterdir()) == ()


def test_container_retains_falsey_injected_repositories() -> None:
    list_repository = FalseyRepository()
    knowledge_repository = FalseyRepository()
    container = Container(
        Settings(_env_file=None),
        local_list_repository=list_repository,
        local_knowledge_repository=knowledge_repository,
    )
    assert container.local_list_repository is list_repository
    assert container.local_knowledge_repository is knowledge_repository
    assert container.structured_list_capability._repository is list_repository
    assert container.structured_knowledge_capability._repository is knowledge_repository


def test_container_composes_one_coordinator_from_existing_paths() -> None:
    container = Container(Settings(_env_file=None))
    coordinator = container.local_first_cognitive_coordinator
    assert coordinator._local_resolver is container.local_first_resolver
    assert coordinator._cognitive_processor is container.cognitive_engine


def test_container_composes_text_routing_from_existing_coordinator() -> None:
    container = Container(Settings(_env_file=None))
    assert (
        container.local_command_text_router._interpreter
        is container.local_command_interpreter
    )
    assert (
        container.local_command_text_router._coordinator
        is container.local_first_cognitive_coordinator
    )


def test_discovery_query_uses_existing_composed_graph() -> None:
    grant = PermissionGrant("a", "w", frozenset((KNOWLEDGE_RECORDS_READ,)))
    container = Container(Settings(_env_file=None), local_permission_grants=(grant,))
    result = container.local_first_resolver.resolve(
        ActorIdentity("a"), WorkspaceIdentity("w"), FindKnowledgeRecordsQuery("key")
    )
    assert result.success and result.records == () and not result.truncated
    assert (
        container.local_first_resolver._knowledge_capability
        is container.structured_knowledge_capability
    )
    assert (
        container.structured_knowledge_capability._repository
        is container.local_knowledge_repository
    )


def _trusted_request(
    binding_key: object = "host-key",
    workspace_id: object = "workspace",
    text: object = "list add x :: a",
) -> TrustedLocalCommandRequest:
    return TrustedLocalCommandRequest(
        TrustedHostRequestInput(binding_key, workspace_id),
        text,
        CognitiveFallbackAuthorization(False),
    )


class RecordingTrustedResolver:
    def __init__(self, resolution: TrustedRequestContextResolution) -> None:
        self.resolution = resolution
        self.requests = []

    def resolve(self, request: TrustedHostRequestInput):
        self.requests.append(request)
        return self.resolution


class FalseyTrustedResolver(RecordingTrustedResolver):
    def __bool__(self) -> bool:
        return False


def test_default_container_composes_inert_trusted_request_path() -> None:
    container = Container(Settings(_env_file=None))
    assert isinstance(
        container.trusted_request_context_resolver,
        ConfiguredTrustedRequestContextResolver,
    )
    assert container.trusted_local_command_routing_service is not None
    assert isinstance(container.membership_repository, InMemoryMembershipRepository)
    assert isinstance(container.membership_decision_service, MembershipDecisionService)
    assert (
        container.membership_decision_service._repository
        is container.membership_repository
    )
    assert (
        container.trusted_local_command_routing_service._membership_service
        is container.membership_decision_service
    )
    assert (
        container.trusted_local_command_routing_service._router
        is container.local_command_text_router
    )
    with patch.object(container.local_command_text_router, "route") as route:
        result = container.trusted_local_command_routing_service.route(
            _trusted_request()
        )
    assert result.trust_resolution.error_code == TRUSTED_CONTEXT_UNKNOWN_BINDING
    assert result.membership_decision is None
    assert result.text_routing_result is None
    route.assert_not_called()


def test_configured_trusted_path_reuses_identities_and_existing_router() -> None:
    actor = ActorIdentity("actor")
    home = WorkspaceIdentity("home")
    work = WorkspaceIdentity("work")
    binding = ConfiguredTrustedHostBinding(
        "host-key",
        actor,
        frozenset(("home", "work")),
    )
    grant = PermissionGrant("actor", "home", frozenset((LIST_ITEMS_ADD,)))
    container = Container(
        Settings(_env_file=None),
        memberships=(
            ActorWorkspaceMembership(actor, home, MembershipStatus.ACTIVE),
            ActorWorkspaceMembership(actor, work, MembershipStatus.ACTIVE),
        ),
        local_permission_grants=(grant,),
        trusted_host_bindings=(binding,),
        trusted_known_workspaces=(work, home),
    )

    with patch.object(
        container.local_command_text_router,
        "route",
        wraps=container.local_command_text_router.route,
    ) as route:
        home_result = container.trusted_local_command_routing_service.route(
            _trusted_request(workspace_id="home")
        )
        work_result = container.trusted_local_command_routing_service.route(
            _trusted_request(workspace_id="work")
        )

    assert home_result.trust_resolution.context.actor is actor
    assert home_result.trust_resolution.context.workspace is home
    assert home_result.text_routing_result.coordinated_result.local_result.success
    assert work_result.trust_resolution.context.workspace is work
    assert (
        work_result.text_routing_result.coordinated_result.local_result.error_code
        == "local_permission_denied"
    )
    assert route.call_count == 2
    assert (
        container.local_permission_policy
        is container.structured_list_capability._permissions
    )


def test_configured_memberships_are_independent_from_permissions() -> None:
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("workspace")
    membership = ActorWorkspaceMembership(
        actor,
        workspace,
        MembershipStatus.ACTIVE,
    )
    container = Container(Settings(_env_file=None), memberships=(membership,))

    assert container.membership_repository.get(actor, workspace) is membership
    assert not container.local_permission_policy.is_allowed(
        actor,
        workspace,
        LIST_ITEMS_ADD,
    )


def test_container_uses_reconstructed_durable_membership_without_grant(
    tmp_path,
) -> None:
    path = tmp_path / "memberships.sqlite3"
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("workspace")
    with SQLiteLocalStorage(path) as first:
        first.initialize()
        first.create(actor, workspace)

    durable = SQLiteLocalStorage(path)
    durable.open()
    durable.initialize()
    try:
        container = Container(
            Settings(_env_file=None),
            membership_repository=durable,
            trusted_host_bindings=(
                ConfiguredTrustedHostBinding(
                    "host-key", actor, frozenset((workspace.workspace_id,))
                ),
            ),
            trusted_known_workspaces=(workspace,),
        )
        result = container.trusted_local_command_routing_service.route(
            _trusted_request()
        )
        assert container.membership_repository is durable
        assert container.membership_decision_service._repository is durable
        assert (
            container.trusted_local_command_routing_service._membership_service
            is container.membership_decision_service
        )
        assert result.membership_decision.membership == durable.get(actor, workspace)
        assert (
            result.text_routing_result.coordinated_result.local_result.error_code
            == "local_permission_denied"
        )
    finally:
        durable.close()


@pytest.mark.parametrize("value", ([], "", b""))
def test_container_rejects_non_tuple_membership_configuration(value) -> None:
    with pytest.raises(ValueError):
        Container(Settings(_env_file=None), memberships=value)


def test_container_rejects_invalid_membership_item() -> None:
    with pytest.raises(ValueError):
        Container(Settings(_env_file=None), memberships=(object(),))


def test_container_retains_falsey_injected_membership_repository() -> None:
    repository = FalseyRepository()
    container = Container(
        Settings(_env_file=None),
        membership_repository=repository,
    )
    assert container.membership_repository is repository
    assert container.membership_decision_service._repository is repository


def test_container_rejects_ambiguous_membership_repository_ownership() -> None:
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("workspace")
    membership = ActorWorkspaceMembership(
        actor,
        workspace,
        MembershipStatus.ACTIVE,
    )
    with pytest.raises(ValueError, match="ambiguous"):
        Container(
            Settings(_env_file=None),
            memberships=(membership,),
            membership_repository=FalseyRepository(),
        )


def test_container_retains_and_uses_exact_injected_trusted_resolver() -> None:
    resolution = TrustedRequestContextResolution(
        False,
        error_code=TRUSTED_CONTEXT_RESOLUTION_FAILED,
    )
    resolver = RecordingTrustedResolver(resolution)
    container = Container(
        Settings(_env_file=None),
        trusted_request_context_resolver=resolver,
    )
    request = _trusted_request()
    result = container.trusted_local_command_routing_service.route(request)
    assert container.trusted_request_context_resolver is resolver
    assert resolver.requests == [request.host_input]
    assert result.trust_resolution is resolution


def test_container_retains_falsey_injected_trusted_resolver() -> None:
    resolver = FalseyTrustedResolver(
        TrustedRequestContextResolution(
            False,
            error_code=TRUSTED_CONTEXT_UNKNOWN_BINDING,
        )
    )
    container = Container(
        Settings(_env_file=None),
        trusted_request_context_resolver=resolver,
    )
    assert container.trusted_request_context_resolver is resolver
    container.trusted_local_command_routing_service.route(_trusted_request())
    assert len(resolver.requests) == 1


@pytest.mark.parametrize(
    "configured",
    (
        {"trusted_host_bindings": (ConfiguredTrustedHostBinding(
            "key", ActorIdentity("actor"), frozenset(("workspace",))
        ),)},
        {"trusted_known_workspaces": (WorkspaceIdentity("workspace"),)},
        {
            "trusted_host_bindings": (ConfiguredTrustedHostBinding(
                "key", ActorIdentity("actor"), frozenset(("workspace",))
            ),),
            "trusted_known_workspaces": (WorkspaceIdentity("workspace"),),
        },
    ),
)
def test_container_rejects_ambiguous_trusted_resolver_ownership(configured) -> None:
    resolver = RecordingTrustedResolver(
        TrustedRequestContextResolution(
            False,
            error_code=TRUSTED_CONTEXT_UNKNOWN_BINDING,
        )
    )
    with pytest.raises(ValueError, match="ambiguous"):
        Container(
            Settings(_env_file=None),
            trusted_request_context_resolver=resolver,
            **configured,
        )


@pytest.mark.parametrize("field", ("trusted_host_bindings", "trusted_known_workspaces"))
@pytest.mark.parametrize("value", ([], "", b""))
def test_container_rejects_non_tuple_trusted_configuration(field, value) -> None:
    with pytest.raises(ValueError):
        Container(Settings(_env_file=None), **{field: value})


def test_trusted_composition_invokes_no_boundary_during_construction() -> None:
    resolver = Mock()
    with (
        patch(
            "app.cognition.interpretation.routing.LocalCommandTextRouter.route"
        ) as route,
        patch(
            "app.cognition.interpretation.interpreter."
            "DeterministicLocalCommandInterpreter.interpret"
        ) as interpret,
        patch(
            "app.cognition.routing.coordinator."
            "LocalFirstCognitiveCoordinator.coordinate"
        ) as coordinate,
        patch(
            "app.cognition.local_resolution.repository."
            "InMemoryListItemRepository.add"
        ) as repository,
        patch("app.cognition.engine.CognitiveEngine.process") as cognitive,
        patch("app.models.ollama_client.OllamaClient.chat") as model,
        patch("requests.get") as network,
    ):
        Container(
            Settings(_env_file=None),
            trusted_request_context_resolver=resolver,
        )
    resolver.resolve.assert_not_called()
    route.assert_not_called()
    interpret.assert_not_called()
    coordinate.assert_not_called()
    repository.assert_not_called()
    cognitive.assert_not_called()
    model.assert_not_called()
    network.assert_not_called()
