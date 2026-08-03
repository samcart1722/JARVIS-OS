"""Application routing proofs for interpreted, invalid and unrelated text."""

from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.interpretation.interpreter import (
    DeterministicLocalCommandInterpreter,
)
from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.interpretation.routing import (
    LocalCommandTextRouter,
    TextRoutingRequest,
    TextRoutingResult,
)
from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import (
    InMemoryKnowledgeRecordRepository,
    InMemoryListItemRepository,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver
from app.cognition.routing.coordinator import LocalFirstCognitiveCoordinator
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedResult,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)
from app.operations.local_command_interpretation_demo_runtime import (
    LocalCommandInterpretationDemoRuntime,
)


def _router(actions=(LIST_ITEMS_ADD, LIST_ITEMS_READ)):
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("workspace")
    grants = (
        (PermissionGrant("actor", "workspace", frozenset(actions)),)
        if actions
        else ()
    )
    policy = ExplicitPermissionPolicy(grants)
    resolver = Mock(
        wraps=LocalFirstResolver(
            StructuredListCapability(InMemoryListItemRepository(), policy),
            StructuredKnowledgeCapability(InMemoryKnowledgeRecordRepository(), policy),
        )
    )
    processor = Mock()
    processor.process.return_value = CognitiveOutcome(True, response="cognitive")
    coordinator = Mock(
        wraps=LocalFirstCognitiveCoordinator(resolver, processor)
    )
    interpreter = Mock(wraps=DeterministicLocalCommandInterpreter())
    return (
        LocalCommandTextRouter(interpreter, coordinator),
        interpreter,
        coordinator,
        resolver,
        processor,
        actor,
        workspace,
    )


def _request(actor, workspace, text, allowed=False):
    return TextRoutingRequest(
        actor, workspace, text, CognitiveFallbackAuthorization(allowed)
    )


def test_interpreted_add_calls_each_boundary_once_and_is_terminal() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router()
    result = router.route(_request(actor, workspace, "list add x :: a", True))
    assert result.coordinated_result.route is CoordinatedRoute.LOCAL
    interpreter.interpret.assert_called_once()
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


def test_invalid_authorized_command_calls_neither_downstream_boundary() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router()
    result = router.route(_request(actor, workspace, "list add x :: | a", True))
    assert result.interpretation.status is LocalCommandInterpretationStatus.INVALID
    assert result.coordinated_result is None
    interpreter.interpret.assert_called_once()
    coordinator.coordinate.assert_not_called()
    resolver.resolve.assert_not_called()
    processor.process.assert_not_called()


def test_unrelated_denied_calls_resolver_once_and_cognitive_zero() -> None:
    router, _, coordinator, resolver, processor, actor, workspace = _router()
    result = router.route(_request(actor, workspace, "hello", False))
    assert result.coordinated_result.route is CoordinatedRoute.SAFE_INSUFFICIENCY
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


def test_unrelated_authorized_calls_cognitive_once() -> None:
    router, _, coordinator, resolver, processor, actor, workspace = _router()
    result = router.route(_request(actor, workspace, "hello", True))
    assert result.coordinated_result.route is CoordinatedRoute.COGNITIVE
    resolver.resolve.assert_called_once()
    processor.process.assert_called_once_with("hello")


def test_router_preserves_exact_coordinated_result_identity() -> None:
    interpreter = DeterministicLocalCommandInterpreter()
    exact_coordinated_result = CoordinatedResult(
        CoordinatedRoute.COGNITIVE,
        cognitive_outcome=CognitiveOutcome(True, response="exact"),
    )
    coordinator = Mock()
    coordinator.coordinate.return_value = exact_coordinated_result
    router = LocalCommandTextRouter(interpreter, coordinator)

    result = router.route(
        TextRoutingRequest(
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            "hello",
            CognitiveFallbackAuthorization(True),
        )
    )

    assert result.coordinated_result is exact_coordinated_result
    coordinator.coordinate.assert_called_once()


def test_permission_denial_and_validation_error_are_preserved() -> None:
    router, _, _, _, processor, actor, workspace = _router(actions=())
    denied = router.route(_request(actor, workspace, "list add x :: a", True))
    invalid_actor = router.route(_request(None, workspace, "list read x", True))
    assert (
        denied.coordinated_result.local_result.error_code
        == "local_permission_denied"
    )
    assert (
        invalid_actor.coordinated_result.local_result.error_code
        == "local_validation_failed"
    )
    processor.process.assert_not_called()


def _safe_insufficiency() -> CoordinatedResult:
    return CoordinatedResult(
        CoordinatedRoute.SAFE_INSUFFICIENCY,
        insufficiency_reason=SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED,
    )


def test_text_routing_result_rejects_invalid_with_coordinated_result() -> None:
    interpretation = LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INVALID,
        invalid_reason=LocalCommandInvalidReason.INVALID_INPUT,
    )
    with pytest.raises(ValueError):
        TextRoutingResult(interpretation, _safe_insufficiency())


@pytest.mark.parametrize(
    "interpretation",
    (
        LocalCommandInterpretation(
            LocalCommandInterpretationStatus.INTERPRETED,
            intent=ReadListItemsQuery("list"),
        ),
        LocalCommandInterpretation(LocalCommandInterpretationStatus.NOT_INTERPRETED),
    ),
)
def test_non_invalid_interpretation_requires_coordinated_result(
    interpretation,
) -> None:
    with pytest.raises(ValueError):
        TextRoutingResult(interpretation)
    with pytest.raises(ValueError):
        TextRoutingResult(interpretation, object())
    assert TextRoutingResult(interpretation, _safe_insufficiency()).coordinated_result


def test_demo_reports_success_from_local_and_cognitive_outcomes() -> None:
    router, _, _, _, _, actor, workspace = _router()
    report = LocalCommandInterpretationDemoRuntime(router, actor, workspace).run()
    assert tuple(scenario.success for scenario in report.scenarios) == (
        True,
        True,
        False,
        False,
        True,
    )
    assert tuple(scenario.cognitive_calls for scenario in report.scenarios) == (
        0,
        0,
        0,
        0,
        1,
    )
