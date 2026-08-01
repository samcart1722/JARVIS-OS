from unittest.mock import Mock

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import (
    InMemoryKnowledgeRecordRepository,
    InMemoryListItemRepository,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver
from app.cognition.routing.coordinator import LocalFirstCognitiveCoordinator
from app.cognition.routing.models import CoordinatedRoute
from app.operations.local_first_cognitive_routing_demo_runtime import (
    LocalFirstCognitiveRoutingDemoRuntime,
)


def test_demo_reports_route_counts_and_observes_one_processor_call() -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")
    permissions = ExplicitPermissionPolicy(
        (
            PermissionGrant(
                actor.actor_id,
                workspace.workspace_id,
                frozenset((LIST_ITEMS_ADD,)),
            ),
        )
    )
    resolver = LocalFirstResolver(
        StructuredListCapability(InMemoryListItemRepository(), permissions),
        StructuredKnowledgeCapability(
            InMemoryKnowledgeRecordRepository(), permissions
        ),
    )
    processor = Mock()
    processor.process.return_value = CognitiveOutcome(True, response="deterministic")
    report = LocalFirstCognitiveRoutingDemoRuntime(
        LocalFirstCognitiveCoordinator(resolver, processor), actor, workspace
    ).run()
    assert report.handled_local.route is CoordinatedRoute.LOCAL
    assert report.denied_fallback.route is CoordinatedRoute.SAFE_INSUFFICIENCY
    assert report.authorized_fallback.route is CoordinatedRoute.COGNITIVE
    assert report.handled_local.cognitive_calls == 0
    assert report.denied_fallback.cognitive_calls == 0
    assert report.authorized_fallback.cognitive_calls == 1
    processor.process.assert_called_once_with("deterministic cognitive demo")
