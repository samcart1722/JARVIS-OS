from unittest.mock import patch

from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    PermissionGrant,
)
from app.core.config import Settings
from app.core.container import Container


class FalseyRepository:
    def __bool__(self) -> bool:
        return False


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
    assert (
        container.structured_knowledge_capability._repository
        is knowledge_repository
    )


def test_container_composes_one_coordinator_from_existing_paths() -> None:
    container = Container(Settings(_env_file=None))
    coordinator = container.local_first_cognitive_coordinator
    assert coordinator._local_resolver is container.local_first_resolver
    assert coordinator._cognitive_processor is container.cognitive_engine
