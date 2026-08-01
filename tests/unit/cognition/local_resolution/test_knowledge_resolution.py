"""Typed, authorized, terminal local knowledge resolution proofs."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock, patch

import pytest

from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.contracts import LocalRepositoryError
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeResolutionResult,
    ReadKnowledgeRecordQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import (
    InMemoryKnowledgeRecordRepository,
    InMemoryListItemRepository,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver


def _record(workspace: WorkspaceIdentity, value: str = "4") -> KnowledgeRecord:
    return KnowledgeRecord(
        "family.child.diaper-size",
        workspace,
        KnowledgeKind.FACT,
        "child.diaper_size",
        value,
        KnowledgeProvenance("user_asserted", "actor:wife"),
    )


def _resolver(repository=None, *actions: str):
    actor = ActorIdentity("wife")
    workspace = WorkspaceIdentity("family-home")
    grants = (
        (PermissionGrant(actor.actor_id, workspace.workspace_id, frozenset(actions)),)
        if actions
        else ()
    )
    permissions = ExplicitPermissionPolicy(grants)
    list_capability = StructuredListCapability(
        InMemoryListItemRepository(), permissions
    )
    knowledge = StructuredKnowledgeCapability(
        repository
        if repository is not None
        else InMemoryKnowledgeRecordRepository(),
        permissions,
    )
    return LocalFirstResolver(list_capability, knowledge), actor, workspace


def test_knowledge_models_normalize_validate_and_are_immutable() -> None:
    workspace = WorkspaceIdentity(" family-home ")
    record = KnowledgeRecord(
        " record ",
        workspace,
        KnowledgeKind.STATE,
        " key ",
        " value ",
        KnowledgeProvenance(" user ", " actor:wife "),
    )
    assert (record.record_id, record.key, record.value) == ("record", "key", "value")
    assert record.provenance == KnowledgeProvenance("user", "actor:wife")
    with pytest.raises(FrozenInstanceError):
        record.value = "changed"


@pytest.mark.parametrize(
    "factory",
    (
        lambda: KnowledgeProvenance("", "reference"),
        lambda: KnowledgeProvenance("source", " "),
        lambda: ReadKnowledgeRecordQuery(""),
        lambda: StoreKnowledgeRecordCommand(None),
    ),
)
def test_knowledge_inputs_reject_invalid_values(factory) -> None:
    with pytest.raises(ValueError):
        factory()


def test_store_read_idempotency_conflict_not_found_and_workspace_identity() -> None:
    repository = InMemoryKnowledgeRecordRepository()
    resolver, actor, workspace = _resolver(
        repository, KNOWLEDGE_RECORDS_ADD, KNOWLEDGE_RECORDS_READ
    )
    record = _record(workspace)
    first = resolver.resolve(actor, workspace, StoreKnowledgeRecordCommand(record))
    second = resolver.resolve(actor, workspace, StoreKnowledgeRecordCommand(record))
    read = resolver.resolve(
        actor, workspace, ReadKnowledgeRecordQuery(record.record_id)
    )
    conflict = resolver.resolve(
        actor,
        workspace,
        StoreKnowledgeRecordCommand(_record(workspace, "5")),
    )
    missing = resolver.resolve(actor, workspace, ReadKnowledgeRecordQuery("missing"))
    other = WorkspaceIdentity("other")
    other_policy = ExplicitPermissionPolicy(
        (PermissionGrant("wife", "other", frozenset((KNOWLEDGE_RECORDS_READ,))),)
    )
    other_resolver = LocalFirstResolver(
        StructuredListCapability(InMemoryListItemRepository(), other_policy),
        StructuredKnowledgeCapability(repository, other_policy),
    )
    isolated = other_resolver.resolve(
        actor, other, ReadKnowledgeRecordQuery(record.record_id)
    )
    assert first.success and first.created
    assert second.success and not second.created
    assert read.record == record and read.record.provenance == record.provenance
    assert conflict.error_code == LOCAL_KNOWLEDGE_CONFLICT
    assert missing.error_code == LOCAL_KNOWLEDGE_NOT_FOUND
    assert isolated.error_code == LOCAL_KNOWLEDGE_NOT_FOUND
    assert all(
        isinstance(result, KnowledgeResolutionResult)
        for result in (first, second, read, conflict, missing, isolated)
    )


@pytest.mark.parametrize(
    "intent",
    (
        StoreKnowledgeRecordCommand(_record(WorkspaceIdentity("family-home"))),
        ReadKnowledgeRecordQuery("family.child.diaper-size"),
    ),
)
def test_knowledge_denial_precedes_repository_access(intent) -> None:
    repository = Mock()
    resolver, actor, workspace = _resolver(repository)
    result = resolver.resolve(actor, workspace, intent)
    assert isinstance(result, KnowledgeResolutionResult)
    assert result.error_code == LOCAL_PERMISSION_DENIED
    repository.store.assert_not_called()
    repository.read.assert_not_called()


def test_invalid_identity_and_workspace_mismatch_never_touch_repository() -> None:
    repository = Mock()
    resolver, actor, workspace = _resolver(repository, KNOWLEDGE_RECORDS_ADD)
    invalid = resolver.resolve(None, workspace, ReadKnowledgeRecordQuery("record"))
    mismatch = resolver.resolve(
        actor,
        workspace,
        StoreKnowledgeRecordCommand(_record(WorkspaceIdentity("other"))),
    )
    assert invalid.error_code == LOCAL_VALIDATION_FAILED
    assert mismatch.error_code == LOCAL_VALIDATION_FAILED
    assert isinstance(invalid, KnowledgeResolutionResult)
    assert isinstance(mismatch, KnowledgeResolutionResult)
    repository.store.assert_not_called()
    repository.read.assert_not_called()


def test_invalid_workspace_and_repository_failure_keep_knowledge_result_type() -> None:
    repository = Mock()
    repository.read.side_effect = LocalRepositoryError("private storage detail")
    resolver, actor, workspace = _resolver(repository, KNOWLEDGE_RECORDS_READ)
    invalid_workspace = resolver.resolve(
        actor, None, ReadKnowledgeRecordQuery("record")
    )
    storage_failure = resolver.resolve(
        actor, workspace, ReadKnowledgeRecordQuery("record")
    )
    assert isinstance(invalid_workspace, KnowledgeResolutionResult)
    assert isinstance(storage_failure, KnowledgeResolutionResult)
    assert invalid_workspace.error_code == LOCAL_VALIDATION_FAILED
    assert storage_failure.error_code == LOCAL_VALIDATION_FAILED
    assert "private storage detail" not in storage_failure.response


def test_knowledge_without_capability_remains_not_handled() -> None:
    permissions = ExplicitPermissionPolicy()
    resolver = LocalFirstResolver(
        StructuredListCapability(InMemoryListItemRepository(), permissions)
    )
    result = resolver.resolve(
        None, None, ReadKnowledgeRecordQuery("record")
    )
    assert not result.handled
    assert not isinstance(result, KnowledgeResolutionResult)


def test_all_local_knowledge_outcomes_make_zero_boundary_calls() -> None:
    resolver, actor, workspace = _resolver(
        None, KNOWLEDGE_RECORDS_ADD, KNOWLEDGE_RECORDS_READ
    )
    record = _record(workspace)
    denied_resolver, denied_actor, denied_workspace = _resolver(None)
    with (
        patch("app.models.ollama_client.OllamaClient.chat") as chat,
        patch("app.models.ollama_readiness_probe.OllamaReadinessProbe.check") as ready,
        patch("requests.get") as network_get,
        patch("requests.post") as network_post,
    ):
        outcomes = (
            resolver.resolve(actor, workspace, StoreKnowledgeRecordCommand(record)),
            resolver.resolve(
                actor, workspace, ReadKnowledgeRecordQuery(record.record_id)
            ),
            resolver.resolve(
                actor,
                workspace,
                StoreKnowledgeRecordCommand(_record(workspace, "different")),
            ),
            resolver.resolve(actor, workspace, ReadKnowledgeRecordQuery("missing")),
            resolver.resolve(None, workspace, ReadKnowledgeRecordQuery("missing")),
            denied_resolver.resolve(
                denied_actor,
                denied_workspace,
                ReadKnowledgeRecordQuery("missing"),
            ),
            resolver.resolve(actor, workspace, object()),
        )
    assert all(not item.model_used and not item.external_access for item in outcomes)
    chat.assert_not_called()
    ready.assert_not_called()
    network_get.assert_not_called()
    network_post.assert_not_called()
