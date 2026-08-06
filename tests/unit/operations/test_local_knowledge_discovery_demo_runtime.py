"""Focused proofs for the Sprint 26 discovery demo runtime."""

from contextlib import ExitStack
from unittest.mock import patch

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    PermissionGrant,
)
from app.core.config import Settings
from app.core.container import Container
from app.operations.local_knowledge_discovery_demo_runtime import (
    LocalKnowledgeDiscoveryDemoRuntime,
)


def test_demo_reports_exact_scenarios_counts_and_boundaries() -> None:
    actor, denied = ActorIdentity("actor"), ActorIdentity("denied")
    workspace = WorkspaceIdentity("home")
    container = Container(
        Settings(REASONING_ENABLED=False, _env_file=None),
        local_permission_grants=(
            PermissionGrant(
                "actor",
                "home",
                frozenset((KNOWLEDGE_RECORDS_ADD, KNOWLEDGE_RECORDS_READ)),
            ),
        ),
    )
    with ExitStack() as stack:
        store = stack.enter_context(
            patch.object(
                container.local_knowledge_repository,
                "store",
                wraps=container.local_knowledge_repository.store,
            )
        )
        read = stack.enter_context(
            patch.object(
                container.local_knowledge_repository,
                "read",
                wraps=container.local_knowledge_repository.read,
            )
        )
        find = stack.enter_context(
            patch.object(
                container.local_knowledge_repository,
                "find_by_key",
                wraps=container.local_knowledge_repository.find_by_key,
            )
        )
        cognitive = stack.enter_context(
            patch.object(
                container.cognitive_engine,
                "process",
                return_value=CognitiveOutcome(True, "fake response"),
            )
        )
        model = stack.enter_context(
            patch.object(container.reasoning_provider, "generate")
        )
        external = stack.enter_context(patch.object(container.ollama_client, "chat"))
        readiness = stack.enter_context(
            patch.object(container.provider_readiness_probe, "check")
        )
        network_get = stack.enter_context(patch("requests.get"))
        network_post = stack.enter_context(patch("requests.post"))
        report = LocalKnowledgeDiscoveryDemoRuntime(
            container.local_command_text_router,
            actor,
            denied,
            workspace,
            store,
            read,
            find,
            cognitive,
            (model,),
            (external,),
            (readiness,),
            (network_get, network_post),
        ).run()
    assert tuple(item.success for item in report.scenarios) == (
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        False,
        True,
    )
    assert tuple(len(item.record_ids) for item in report.scenarios) == (
        0,
        0,
        2,
        2,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    assert report.scenarios[2].record_ids == ("diaper-a", "diaper-b")
    assert all(not item.truncated for item in report.scenarios)
    assert tuple(item.cognitive_calls for item in report.scenarios) == (
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
    )
    assert report.store_calls == 2
    assert report.read_calls == 0
    assert report.find_calls == 4
    assert report.total_repository_operations == 6
    assert report.cognitive_calls == 1
    read.assert_not_called()
    model.assert_not_called()
    external.assert_not_called()
    readiness.assert_not_called()
    network_get.assert_not_called()
    network_post.assert_not_called()
