"""Sprint 26 exact local knowledge discovery proofs."""

import inspect
from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.contracts import (
    KnowledgeRecordRepository,
    LocalRepositoryError,
)
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    KNOWLEDGE_DISCOVERY_LOOKAHEAD,
    KNOWLEDGE_DISCOVERY_MAX_RESULTS,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    FindKnowledgeRecordsQuery,
    KnowledgeDiscoveryResolutionResult,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeRecordsFound,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import (
    InMemoryKnowledgeRecordRepository,
    InMemoryListItemRepository,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver


def _record(workspace, record_id, key="child.diaper_size", kind=KnowledgeKind.FACT):
    return KnowledgeRecord(
        record_id,
        workspace,
        kind,
        key,
        "4",
        KnowledgeProvenance("user_asserted", f"actor:{record_id}"),
    )


def _resolver(repository, allowed=True):
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("home")
    grants = (
        (PermissionGrant("actor", "home", frozenset((KNOWLEDGE_RECORDS_READ,))),)
        if allowed
        else ()
    )
    policy = ExplicitPermissionPolicy(grants)
    return (
        LocalFirstResolver(
            StructuredListCapability(InMemoryListItemRepository(), policy),
            StructuredKnowledgeCapability(repository, policy),
        ),
        actor,
        workspace,
    )


def test_query_and_found_models_are_immutable_and_enforce_contracts() -> None:
    query = FindKnowledgeRecordsQuery(" child.diaper_size ", KnowledgeKind.FACT)
    assert query.key == "child.diaper_size" and query.kind is KnowledgeKind.FACT
    with pytest.raises(FrozenInstanceError):
        query.key = "changed"
    for invalid in ("", " "):
        with pytest.raises(ValueError):
            FindKnowledgeRecordsQuery(invalid)
    with pytest.raises(ValueError):
        FindKnowledgeRecordsQuery("key", "fact")
    assert KnowledgeRecordsFound((), False).records == ()
    with pytest.raises(ValueError):
        KnowledgeRecordsFound([], False)
    with pytest.raises(ValueError):
        KnowledgeRecordsFound((object(),), False)
    workspace = WorkspaceIdentity("home")
    fifty = tuple(_record(workspace, f"r-{number:02}") for number in range(50))
    assert not KnowledgeRecordsFound(fifty, False).truncated
    assert KnowledgeRecordsFound(fifty, True).truncated
    with pytest.raises(ValueError):
        KnowledgeRecordsFound(fifty + (_record(workspace, "r-50"),), False)
    with pytest.raises(ValueError):
        KnowledgeRecordsFound((), True)
    with pytest.raises(ValueError):
        KnowledgeRecordsFound((), 0)


def test_repository_protocol_has_exact_bounded_signature() -> None:
    signature = inspect.signature(KnowledgeRecordRepository.find_by_key)
    assert tuple(signature.parameters) == ("self", "workspace", "key", "kind")
    assert signature.parameters["kind"].default is None
    assert KNOWLEDGE_DISCOVERY_MAX_RESULTS == 50
    assert KNOWLEDGE_DISCOVERY_LOOKAHEAD == 51


def test_in_memory_exact_kind_order_workspace_identity_and_lookahead() -> None:
    repository = InMemoryKnowledgeRecordRepository()
    workspace, other = WorkspaceIdentity("home"), WorkspaceIdentity("other")
    ordered_ids = ("A", "r-10", "r-2", "z", "Á")
    inserted = tuple(
        _record(workspace, record_id, kind=KnowledgeKind.FACT)
        for record_id in reversed(ordered_ids)
    )
    for record in inserted:
        repository.store(record)
    repository.store(_record(workspace, "concept", kind=KnowledgeKind.CONCEPT))
    repository.store(_record(workspace, "substring", key="child.diaper"))
    repository.store(_record(workspace, "case", key="CHILD.DIAPER_SIZE"))
    repository.store(_record(other, "other"))
    found = repository.find_by_key(workspace, "child.diaper_size", KnowledgeKind.FACT)
    assert tuple(record.record_id for record in found) == tuple(sorted(ordered_ids))
    assert all(any(record is original for original in inserted) for record in found)
    assert repository.find_by_key(workspace, "missing") == ()
    assert tuple(
        record.record_id
        for record in repository.find_by_key(
            workspace, "child.diaper_size", KnowledgeKind.CONCEPT
        )
    ) == ("concept",)
    assert all(
        record.workspace == workspace
        for record in repository.find_by_key(workspace, "child.diaper_size")
    )
    for number in range(60):
        repository.store(_record(workspace, f"bulk-{number:02}", key="bulk"))
    assert len(repository.find_by_key(workspace, "bulk")) == 51


@pytest.mark.parametrize(
    ("total", "repository_count", "visible_count", "truncated"),
    (
        (49, 49, 49, False),
        (50, 50, 50, False),
        (51, 51, 50, True),
        (52, 51, 50, True),
    ),
)
def test_in_memory_boundary_matrix_through_real_capability(
    total, repository_count, visible_count, truncated
) -> None:
    repository = InMemoryKnowledgeRecordRepository()
    actor = ActorIdentity("actor")
    workspace, other = WorkspaceIdentity("home"), WorkspaceIdentity("other")
    for number in reversed(range(total)):
        repository.store(_record(workspace, f"match-{number:03}", key="boundary.key"))
    repository.store(_record(workspace, "other-key", key="boundary"))
    repository.store(
        _record(
            workspace,
            "other-kind",
            key="boundary.key",
            kind=KnowledgeKind.CONCEPT,
        )
    )
    repository.store(_record(other, "other-workspace", key="boundary.key"))

    repository_records = repository.find_by_key(
        workspace, "boundary.key", KnowledgeKind.FACT
    )
    policy = ExplicitPermissionPolicy(
        (
            PermissionGrant(
                actor.actor_id,
                workspace.workspace_id,
                frozenset((KNOWLEDGE_RECORDS_READ,)),
            ),
        )
    )
    result = StructuredKnowledgeCapability(repository, policy).execute(
        actor,
        workspace,
        FindKnowledgeRecordsQuery("boundary.key", KnowledgeKind.FACT),
    )

    expected_ids = tuple(f"match-{number:03}" for number in range(total))
    assert len(repository_records) == repository_count <= 51
    assert tuple(record.record_id for record in repository_records) == expected_ids[:51]
    assert len(result.records) == visible_count <= 50
    assert tuple(record.record_id for record in result.records) == expected_ids[:50]
    assert result.truncated is truncated
    assert all(
        record.workspace == workspace
        and record.key == "boundary.key"
        and record.kind is KnowledgeKind.FACT
        for record in (*repository_records, *result.records)
    )


def test_capability_authorizes_once_before_one_find_and_preserves_records() -> None:
    repository = Mock()
    workspace = WorkspaceIdentity("home")
    records = tuple(_record(workspace, f"r-{number:02}") for number in range(51))
    repository.find_by_key.return_value = records
    permissions = Mock()
    permissions.is_allowed.return_value = True
    capability = StructuredKnowledgeCapability(repository, permissions)
    result = capability.execute(
        ActorIdentity("actor"),
        workspace,
        FindKnowledgeRecordsQuery("child.diaper_size"),
    )
    permissions.is_allowed.assert_called_once_with(
        ActorIdentity("actor"), workspace, KNOWLEDGE_RECORDS_READ
    )
    repository.find_by_key.assert_called_once_with(workspace, "child.diaper_size", None)
    assert result == KnowledgeRecordsFound(records[:50], True)
    assert all(result.records[index] is records[index] for index in range(50))


def test_resolver_zero_multiple_denied_invalid_and_failure_are_terminal() -> None:
    repository = InMemoryKnowledgeRecordRepository()
    resolver, actor, workspace = _resolver(repository)
    first, second = _record(workspace, "a"), _record(workspace, "b")
    repository.store(second)
    repository.store(first)
    multiple = resolver.resolve(
        actor, workspace, FindKnowledgeRecordsQuery("child.diaper_size")
    )
    zero = resolver.resolve(actor, workspace, FindKnowledgeRecordsQuery("missing"))
    assert isinstance(multiple, KnowledgeDiscoveryResolutionResult)
    assert (
        multiple.success
        and multiple.records == (first, second)
        and not multiple.truncated
    )
    assert zero.success and zero.records == () and zero.error_code is None

    denied_repository = Mock()
    denied, denied_actor, denied_workspace = _resolver(denied_repository, False)
    denied_result = denied.resolve(
        denied_actor, denied_workspace, FindKnowledgeRecordsQuery("key")
    )
    assert denied_result.error_code == LOCAL_PERMISSION_DENIED
    denied_repository.find_by_key.assert_not_called()

    invalid = resolver.resolve(None, workspace, FindKnowledgeRecordsQuery("key"))
    assert invalid.error_code == LOCAL_VALIDATION_FAILED
    failing = Mock()
    failing.find_by_key.side_effect = LocalRepositoryError("private")
    failure_resolver, _, _ = _resolver(failing)
    failure = failure_resolver.resolve(
        actor, workspace, FindKnowledgeRecordsQuery("key")
    )
    assert failure.error_code == LOCAL_VALIDATION_FAILED
    assert "private" not in failure.response


def test_discovery_result_rejects_remote_and_failed_payloads() -> None:
    workspace = WorkspaceIdentity("home")
    record = _record(workspace, "r")
    with pytest.raises(ValueError):
        KnowledgeDiscoveryResolutionResult(
            True, False, "failed", "local_capability", (record,)
        )
    with pytest.raises(ValueError):
        KnowledgeDiscoveryResolutionResult(
            True, True, "ok", "local_capability", model_used=True
        )
