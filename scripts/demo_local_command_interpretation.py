"""Thin Container adapter for the Sprint 24 text-routing demo."""

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    PermissionGrant,
)
from app.core.config import Settings
from app.core.container import Container
from app.operations.local_command_interpretation_demo_runtime import (
    LocalCommandInterpretationDemoRuntime,
)


def main() -> int:
    title = "Luxiom Deterministic Local Command Interpretation Demo v1"
    try:
        actor = ActorIdentity("text-demo-actor")
        workspace = WorkspaceIdentity("text-demo-workspace")
        grant = PermissionGrant(
            actor.actor_id,
            workspace.workspace_id,
            frozenset((LIST_ITEMS_ADD, LIST_ITEMS_READ)),
        )
        container = Container(
            Settings(REASONING_ENABLED=False, _env_file=None),
            local_permission_grants=(grant,),
        )
        report = LocalCommandInterpretationDemoRuntime(
            container.local_command_text_router, actor, workspace
        ).run()
        print(title)
        for number, scenario in enumerate(report.scenarios, start=1):
            print(f"Scenario {number}")
            print(f"Interpretation: {scenario.interpretation_status.value}")
            print(f"Route: {scenario.route.value if scenario.route else 'terminal'}")
            print(f"Success: {str(scenario.success).lower()}")
            print(f"Items: {' | '.join(scenario.items)}")
            print(f"Cognitive calls: {scenario.cognitive_calls}")
        print(f"Model calls: {report.model_calls}")
        print(f"External calls: {report.external_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        return 0
    except Exception:
        print(title)
        print("Text-routing demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
