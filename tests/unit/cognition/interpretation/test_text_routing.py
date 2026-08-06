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
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_PERMISSION_DENIED,
    ActorIdentity,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
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
        (PermissionGrant("actor", "workspace", frozenset(actions)),) if actions else ()
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
    coordinator = Mock(wraps=LocalFirstCognitiveCoordinator(resolver, processor))
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
    interpreter.interpret.assert_called_once_with("list add x :: a", workspace)
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


def test_valid_find_calls_existing_boundaries_and_repository_once() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router(
        (KNOWLEDGE_RECORDS_READ,)
    )
    repository = resolver._mock_wraps._knowledge_capability._repository
    repository.find_by_key = Mock(wraps=repository.find_by_key)
    text = 'knowledge find :: {"key":"missing"}'
    result = router.route(_request(actor, workspace, text, True))
    local = result.coordinated_result.local_result
    assert result.coordinated_result.route is CoordinatedRoute.LOCAL
    assert local.success and local.records == () and not local.truncated
    interpreter.interpret.assert_called_once_with(text, workspace)
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    repository.find_by_key.assert_called_once_with(workspace, "missing", None)
    processor.process.assert_not_called()


def test_invalid_find_is_terminal_before_coordination() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router(
        (KNOWLEDGE_RECORDS_READ,)
    )
    text = "knowledge find :: {"
    result = router.route(_request(actor, workspace, text, True))
    assert result.interpretation.status is LocalCommandInterpretationStatus.INVALID
    assert result.coordinated_result is None
    interpreter.interpret.assert_called_once_with(text, workspace)
    coordinator.coordinate.assert_not_called()
    resolver.resolve.assert_not_called()
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
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router()
    result = router.route(_request(actor, workspace, "hello", False))
    assert result.coordinated_result.route is CoordinatedRoute.SAFE_INSUFFICIENCY
    interpreter.interpret.assert_called_once_with("hello", workspace)
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


def test_unrelated_authorized_calls_cognitive_once() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router()
    result = router.route(_request(actor, workspace, "hello", True))
    assert result.coordinated_result.route is CoordinatedRoute.COGNITIVE
    interpreter.interpret.assert_called_once_with("hello", workspace)
    coordinator.coordinate.assert_called_once()
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
        denied.coordinated_result.local_result.error_code == "local_permission_denied"
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


def _knowledge_store(value="4") -> str:
    return (
        'knowledge store :: {"record_id":"record one","kind":"fact",'
        f'"key":"key","value":"{value}","source_type":"user_asserted",'
        '"source_reference":"actor:actor"}'
    )


def test_knowledge_store_read_duplicate_conflict_and_not_found_are_terminal() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router(
        (KNOWLEDGE_RECORDS_ADD, KNOWLEDGE_RECORDS_READ)
    )
    stored = router.route(_request(actor, workspace, _knowledge_store(), True))
    interpreter.interpret.assert_called_once_with(_knowledge_store(), workspace)
    coordinated_request = coordinator.coordinate.call_args.args[0]
    interpreted_command = stored.interpretation.intent
    assert isinstance(interpreted_command, StoreKnowledgeRecordCommand)
    assert coordinated_request.local_intent is interpreted_command
    assert stored.coordinated_result.local_result.record is interpreted_command.record

    duplicate = router.route(_request(actor, workspace, _knowledge_store(), True))
    read = router.route(
        _request(
            actor,
            workspace,
            'knowledge read :: {"record_id":"record one"}',
            True,
        )
    )
    conflict = router.route(
        _request(actor, workspace, _knowledge_store("different"), True)
    )
    missing = router.route(
        _request(actor, workspace, 'knowledge read :: {"record_id":"missing"}', True)
    )

    assert stored.coordinated_result.route is CoordinatedRoute.LOCAL
    assert stored.coordinated_result.local_result.created
    assert not duplicate.coordinated_result.local_result.created
    assert read.coordinated_result.local_result.record is interpreted_command.record
    assert read.coordinated_result.local_result.record.provenance.source_reference == (
        "actor:actor"
    )
    assert conflict.coordinated_result.local_result.error_code == (
        LOCAL_KNOWLEDGE_CONFLICT
    )
    assert missing.coordinated_result.local_result.error_code == (
        LOCAL_KNOWLEDGE_NOT_FOUND
    )
    assert interpreter.interpret.call_count == 5
    assert coordinator.coordinate.call_count == 5
    assert resolver.resolve.call_count == 5
    processor.process.assert_not_called()


def test_knowledge_denial_is_terminal_and_malformed_stops_before_routing() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router()
    repository = resolver._mock_wraps._knowledge_capability._repository
    denied = router.route(_request(actor, workspace, _knowledge_store(), True))
    assert denied.coordinated_result.local_result.error_code == LOCAL_PERMISSION_DENIED
    assert repository._records == {}
    malformed = router.route(_request(actor, workspace, "knowledge store :: {", True))
    assert malformed.coordinated_result is None
    assert interpreter.interpret.call_count == 2
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


@pytest.mark.parametrize(
    ("actor", "workspace"),
    ((None, WorkspaceIdentity("workspace")), (ActorIdentity("actor"), None)),
)
def test_knowledge_read_invalid_identity_is_terminal(actor, workspace) -> None:
    router, _, coordinator, resolver, processor, _, _ = _router(
        (KNOWLEDGE_RECORDS_READ,)
    )
    result = router.route(
        _request(actor, workspace, 'knowledge read :: {"record_id":"record"}', True)
    )
    assert result.coordinated_result.local_result.error_code == (
        "local_validation_failed"
    )
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


@pytest.mark.parametrize(
    "case",
    ("first_store", "identical_store", "read", "conflict", "not_found", "denied"),
)
def test_each_knowledge_operation_has_exact_local_call_profile(case) -> None:
    actions = (
        ()
        if case == "denied"
        else (
            KNOWLEDGE_RECORDS_ADD,
            KNOWLEDGE_RECORDS_READ,
        )
    )
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router(
        actions
    )
    if case in {"identical_store", "read", "conflict"}:
        router.route(_request(actor, workspace, _knowledge_store()))
        for observed in (interpreter, coordinator, resolver, processor):
            observed.reset_mock()

    if case in {"first_store", "identical_store", "denied"}:
        text = _knowledge_store()
    elif case == "read":
        text = 'knowledge read :: {"record_id":"record one"}'
    elif case == "conflict":
        text = _knowledge_store("different")
    else:
        text = 'knowledge read :: {"record_id":"missing"}'

    repository = resolver._mock_wraps._knowledge_capability._repository
    before_records = dict(repository._records)
    result = router.route(_request(actor, workspace, text, True))

    interpreter.interpret.assert_called_once_with(text, workspace)
    coordinator.coordinate.assert_called_once()
    resolver.resolve.assert_called_once()
    processor.process.assert_not_called()
    local = result.coordinated_result.local_result
    if case == "first_store":
        assert local.success and local.created
    elif case == "identical_store":
        assert local.success and not local.created
    elif case == "read":
        assert local.success and local.record.record_id == "record one"
    elif case == "conflict":
        assert local.error_code == LOCAL_KNOWLEDGE_CONFLICT
    elif case == "not_found":
        assert local.error_code == LOCAL_KNOWLEDGE_NOT_FOUND
    else:
        assert local.error_code == LOCAL_PERMISSION_DENIED
        assert repository._records == before_records


def test_malformed_authorized_has_exact_zero_downstream_profile() -> None:
    router, interpreter, coordinator, resolver, processor, actor, workspace = _router()
    text = "knowledge store :: {"
    result = router.route(_request(actor, workspace, text, True))
    assert result.coordinated_result is None
    interpreter.interpret.assert_called_once_with(text, workspace)
    coordinator.coordinate.assert_not_called()
    resolver.resolve.assert_not_called()
    processor.process.assert_not_called()
