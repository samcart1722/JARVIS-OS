"""Focused proofs for the Sprint 25 operational runtime."""

from contextlib import ExitStack
from unittest.mock import patch

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    PermissionGrant,
)
from app.core.config import Settings
from app.core.container import Container
from app.operations.local_knowledge_command_demo_runtime import (
    LocalKnowledgeCommandDemoRuntime,
)


def test_demo_reports_all_terminal_and_fallback_scenarios() -> None:
    actor = ActorIdentity("knowledge-demo-actor")
    denied = ActorIdentity("denied-knowledge-demo-actor")
    workspace = WorkspaceIdentity("knowledge-demo-workspace")
    grant = PermissionGrant(
        actor.actor_id,
        workspace.workspace_id,
        frozenset((KNOWLEDGE_RECORDS_ADD, KNOWLEDGE_RECORDS_READ)),
    )
    container = Container(
        Settings(REASONING_ENABLED=False, _env_file=None),
        local_permission_grants=(grant,),
    )
    with ExitStack() as stack:
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
        external = stack.enter_context(
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
        report = LocalKnowledgeCommandDemoRuntime(
            container.local_command_text_router,
            actor,
            denied,
            workspace,
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
        False,
        False,
        False,
        False,
        False,
        True,
    )
    assert tuple(item.created for item in report.scenarios) == (
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    )
    assert tuple(item.cognitive_calls for item in report.scenarios) == (
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
    assert all(
        count == 0
        for count in (
            report.model_calls,
            report.external_calls,
            report.readiness_calls,
            report.network_calls,
        )
    )
    assert cognitive.call_count == 1
    model.assert_not_called()
    external.assert_not_called()
    readiness.assert_not_called()
    network_get.assert_not_called()
    network_post.assert_not_called()
