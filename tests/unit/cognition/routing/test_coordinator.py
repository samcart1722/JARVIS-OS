"""Deterministic explicit local-first coordination proofs."""

from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    ReadKnowledgeRecordQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
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
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRequest,
    CoordinatedResult,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)


def _components(*actions: str):
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")
    permissions = ExplicitPermissionPolicy(
        (PermissionGrant("actor", "workspace", frozenset(actions)),)
        if actions
        else ()
    )
    resolver = LocalFirstResolver(
        StructuredListCapability(InMemoryListItemRepository(), permissions),
        StructuredKnowledgeCapability(
            InMemoryKnowledgeRecordRepository(), permissions
        ),
    )
    processor = Mock()
    processor.process.return_value = CognitiveOutcome(True, response="cognitive")
    return resolver, processor, actor, workspace


def _request(actor, workspace, intent, allowed=False, cognitive_input=None):
    return CoordinatedRequest(
        actor,
        workspace,
        intent,
        CognitiveFallbackAuthorization(allowed),
        cognitive_input,
    )


def _knowledge(workspace: WorkspaceIdentity, value: str = "value"):
    return KnowledgeRecord(
        "record",
        workspace,
        KnowledgeKind.FACT,
        "key",
        value,
        KnowledgeProvenance("user_asserted", "actor:actor"),
    )


def test_handled_list_success_is_terminal_and_preserves_exact_result() -> None:
    resolver, processor, actor, workspace = _components(LIST_ITEMS_ADD)
    observed_resolver = Mock(wraps=resolver)
    coordinator = LocalFirstCognitiveCoordinator(observed_resolver, processor)
    result = coordinator.coordinate(
        _request(actor, workspace, AddListItemsCommand("list", ("item",)), True, "x")
    )
    assert result.route is CoordinatedRoute.LOCAL
    assert result.local_result.success
    observed_resolver.resolve.assert_called_once()
    processor.process.assert_not_called()


def test_list_denial_and_validation_failure_are_terminal() -> None:
    resolver, processor, actor, workspace = _components()
    coordinator = LocalFirstCognitiveCoordinator(resolver, processor)
    denied = coordinator.coordinate(
        _request(actor, workspace, AddListItemsCommand("list", ("item",)), True, "x")
    )
    invalid = coordinator.coordinate(
        _request(None, workspace, AddListItemsCommand("list", ("item",)), True, "x")
    )
    assert denied.route is invalid.route is CoordinatedRoute.LOCAL
    assert not denied.local_result.success and not invalid.local_result.success
    processor.process.assert_not_called()


def test_knowledge_success_not_found_and_conflict_are_terminal() -> None:
    resolver, processor, actor, workspace = _components(
        KNOWLEDGE_RECORDS_ADD, KNOWLEDGE_RECORDS_READ
    )
    coordinator = LocalFirstCognitiveCoordinator(resolver, processor)
    record = _knowledge(workspace)
    stored = coordinator.coordinate(
        _request(actor, workspace, StoreKnowledgeRecordCommand(record), True, "x")
    )
    missing = coordinator.coordinate(
        _request(actor, workspace, ReadKnowledgeRecordQuery("missing"), True, "x")
    )
    conflict = coordinator.coordinate(
        _request(
            actor,
            workspace,
            StoreKnowledgeRecordCommand(_knowledge(workspace, "different")),
            True,
            "x",
        )
    )
    assert all(
        item.route is CoordinatedRoute.LOCAL
        for item in (stored, missing, conflict)
    )
    assert stored.local_result.success
    assert not missing.local_result.success and not conflict.local_result.success
    processor.process.assert_not_called()


def test_unsupported_denied_fallback_is_safe_insufficiency() -> None:
    resolver, processor, actor, workspace = _components()
    result = LocalFirstCognitiveCoordinator(resolver, processor).coordinate(
        _request(actor, workspace, object(), False, "valid")
    )
    assert result.route is CoordinatedRoute.SAFE_INSUFFICIENCY
    assert (
        result.insufficiency_reason
        is SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED
    )
    processor.process.assert_not_called()


@pytest.mark.parametrize("cognitive_input", (None, "", "  ", object()))
def test_unsupported_authorized_invalid_input_is_safe_insufficiency(
    cognitive_input,
) -> None:
    resolver, processor, actor, workspace = _components()
    result = LocalFirstCognitiveCoordinator(resolver, processor).coordinate(
        _request(actor, workspace, object(), True, cognitive_input)
    )
    assert result.route is CoordinatedRoute.SAFE_INSUFFICIENCY
    assert (
        result.insufficiency_reason
        is SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID
    )
    processor.process.assert_not_called()


def test_authorized_valid_fallback_calls_once_and_preserves_outcome_identity() -> None:
    resolver, processor, actor, workspace = _components()
    expected = CognitiveOutcome(True, response="exact outcome")
    processor.process.return_value = expected
    observed_resolver = Mock(wraps=resolver)
    result = LocalFirstCognitiveCoordinator(
        observed_resolver, processor
    ).coordinate(_request(actor, workspace, object(), True, " cognitive input "))
    assert result.route is CoordinatedRoute.COGNITIVE
    assert result.cognitive_outcome is expected
    observed_resolver.resolve.assert_called_once()
    processor.process.assert_called_once_with(" cognitive input ")


def test_authorization_requires_an_explicit_boolean() -> None:
    with pytest.raises(ValueError):
        CognitiveFallbackAuthorization(1)


@pytest.mark.parametrize(
    "result",
    (
        lambda: CoordinatedResult(CoordinatedRoute.LOCAL),
        lambda: CoordinatedResult(
            CoordinatedRoute.COGNITIVE,
            cognitive_outcome=CognitiveOutcome(True, response="ok"),
            insufficiency_reason=SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID,
        ),
        lambda: CoordinatedResult(CoordinatedRoute.SAFE_INSUFFICIENCY),
    ),
)
def test_result_invariants_reject_contradictory_payloads(result) -> None:
    with pytest.raises(ValueError):
        result()
