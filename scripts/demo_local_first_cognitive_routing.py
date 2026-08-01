"""Thin Container adapter for the explicit routing coordinator demo."""

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    PermissionGrant,
)
from app.core.config import Settings
from app.core.container import Container
from app.operations.local_first_cognitive_routing_demo_runtime import (
    LocalFirstCognitiveRoutingDemoRuntime,
)


def main() -> int:
    title = "Luxiom Explicit Local-First Cognitive Routing Demo v1"
    try:
        actor = ActorIdentity("routing-demo-actor")
        workspace = WorkspaceIdentity("routing-demo-workspace")
        grant = PermissionGrant(
            actor.actor_id,
            workspace.workspace_id,
            frozenset((LIST_ITEMS_ADD,)),
        )
        container = Container(
            Settings(REASONING_ENABLED=False, _env_file=None),
            local_permission_grants=(grant,),
        )
        report = LocalFirstCognitiveRoutingDemoRuntime(
            container.local_first_cognitive_coordinator,
            actor,
            workspace,
        ).run()
        print(title)
        for number, scenario in enumerate(
            (
                report.handled_local,
                report.denied_fallback,
                report.authorized_fallback,
            ),
            start=1,
        ):
            print(f"Scenario {number}")
            print(f"Route: {scenario.route.value}")
            print(f"Local handled: {str(scenario.local_handled).lower()}")
            print(
                "Fallback authorized: "
                f"{str(scenario.fallback_authorized).lower()}"
            )
            print(f"Cognitive calls: {scenario.cognitive_calls}")
        print(f"Model calls: {report.model_calls}")
        print(f"External calls: {report.external_calls}")
        print(f"Readiness calls: {report.readiness_calls}")
        print(f"Network calls: {report.network_calls}")
        return 0
    except Exception:
        print(title)
        print("Routing demo failed safely.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
