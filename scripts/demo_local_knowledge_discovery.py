"""Thin Container adapter for the Sprint 26 knowledge-discovery demo."""

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


def main() -> int:
    title = "Luxiom Deterministic Local Knowledge Discovery Demo v1"
    try:
        actor = ActorIdentity("discovery-demo-actor")
        denied = ActorIdentity("denied-discovery-demo-actor")
        workspace = WorkspaceIdentity("discovery-demo-workspace")
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
                    return_value=CognitiveOutcome(
                        True, "local demo cognitive response"
                    ),
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
        print(title)
        for number, scenario in enumerate(report.scenarios, 1):
            route = scenario.route.value if scenario.route else "terminal"
            print(
                f"Scenario {number}: {scenario.interpretation_status.value} / {route}"
            )
            print(f"Success: {str(scenario.success).lower()}")
            print(f"Error code: {scenario.error_code or 'none'}")
            print(f"Record IDs: {','.join(scenario.record_ids) or 'none'}")
            print(f"Truncated: {str(scenario.truncated).lower()}")
            print(f"Cognitive calls: {scenario.cognitive_calls}")
        print(f"Store calls: {report.store_calls}")
        print(f"Read calls: {report.read_calls}")
        print(f"Find calls: {report.find_calls}")
        print(f"Total repository operations: {report.total_repository_operations}")
        print(f"Cognitive calls: {report.cognitive_calls}")
        print(f"Model calls: {report.model_calls}")
        print(f"External calls: {report.external_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        return 0
    except Exception:
        print(title)
        print("Knowledge-discovery demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
