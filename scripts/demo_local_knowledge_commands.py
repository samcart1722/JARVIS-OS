"""Thin Container adapter for the Sprint 25 knowledge-command demo."""

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


def main() -> int:
    title = "Luxiom Deterministic Local Knowledge Commands Demo v1"
    try:
        actor = ActorIdentity("knowledge-demo-actor")
        denied_actor = ActorIdentity("denied-knowledge-demo-actor")
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
                denied_actor,
                workspace,
                cognitive,
                (model,),
                (external,),
                (readiness,),
                (network_get, network_post),
            ).run()
        print(title)
        for number, scenario in enumerate(report.scenarios, start=1):
            print(f"Scenario {number}")
            print(f"Interpretation: {scenario.interpretation_status.value}")
            print(f"Route: {scenario.route.value if scenario.route else 'terminal'}")
            print(f"Success: {str(scenario.success).lower()}")
            print(f"Created: {str(scenario.created).lower()}")
            print(f"Error code: {scenario.error_code or 'none'}")
            if scenario.record is not None:
                print(f"Record ID: {scenario.record.record_id}")
                print(f"Source type: {scenario.record.provenance.source_type}")
                print(
                    "Source reference: "
                    f"{scenario.record.provenance.source_reference}"
                )
            print(f"Cognitive calls: {scenario.cognitive_calls}")
        print(f"Model calls: {report.model_calls}")
        print(f"External calls: {report.external_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        return 0
    except Exception:
        print(title)
        print("Knowledge-command demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
