"""Standalone continuation capability and equivalent memory/SQLite behavior."""

import sqlite3
from dataclasses import fields
from unittest.mock import Mock

import pytest

from app.cognition.local_resolution.capability import LocalPermissionDenied
from app.cognition.local_resolution.contracts import (
    KnowledgeBrowseAfterRepository,
    LocalRepositoryError,
    PermissionGrantRepositoryError,
    PermissionPolicy,
)
from app.cognition.local_resolution.knowledge_browse_after_capability import (
    StructuredKnowledgeBrowseAfterCapability,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    BrowseAfterKnowledgeRecordsQuery,
    BrowseKnowledgeRecordsQuery,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeRecordSummary,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_BROWSE,
    KNOWLEDGE_RECORDS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
    RepositoryPermissionPolicy,
)
from app.cognition.local_resolution.repository import InMemoryKnowledgeRecordRepository
from app.infrastructure.local_storage.sqlite_storage import (
    LocalStorageError,
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
)

ACTOR = ActorIdentity("actor")
WORKSPACE = WorkspaceIdentity("selected")
OTHER = WorkspaceIdentity("other")
QUERY = BrowseAfterKnowledgeRecordsQuery(" m ")


def record(identifier, workspace=WORKSPACE):
    return KnowledgeRecord(
        identifier,
        workspace,
        KnowledgeKind.FACT,
        "key",
        "private value",
        KnowledgeProvenance("private source", "private reference"),
    )


def summary(identifier, workspace=WORKSPACE):
    return KnowledgeRecordSummary(identifier, workspace, KnowledgeKind.FACT, "key")


def capability(rows=()):
    repository = Mock(spec=KnowledgeBrowseAfterRepository)
    repository.browse_after.return_value = rows
    policy = Mock(spec=PermissionPolicy)
    policy.is_allowed.return_value = True
    return (
        StructuredKnowledgeBrowseAfterCapability(repository, policy),
        repository,
        policy,
    )


@pytest.mark.parametrize("count", (0, 1, 49, 50, 51))
def test_authorize_then_one_call_and_exact_truncation(count):
    rows = tuple(summary(f"r-{i:03}") for i in range(count))
    service, repository, policy = capability(rows)
    events = []
    policy.is_allowed.side_effect = lambda *args: events.append("permission") or True
    repository.browse_after.side_effect = lambda *args: events.append("data") or rows
    result = service.execute(ACTOR, WORKSPACE, QUERY)
    assert events == ["permission", "data"]
    policy.is_allowed.assert_called_once_with(
        ACTOR, WORKSPACE, KNOWLEDGE_RECORDS_BROWSE
    )
    repository.browse_after.assert_called_once_with(WORKSPACE, "m")
    assert result.records == rows[:50]
    assert result.truncated is (count == 51)


@pytest.mark.parametrize("allowed", (False, None, 0, 1, "true", [], object()))
def test_only_literal_true_authorizes(allowed):
    service, repository, policy = capability()
    policy.is_allowed.return_value = allowed
    with pytest.raises(LocalPermissionDenied):
        service.execute(ACTOR, WORKSPACE, QUERY)
    repository.browse_after.assert_not_called()


@pytest.mark.parametrize("failure", (PermissionGrantRepositoryError, RuntimeError))
def test_permission_dependency_exception_never_reaches_data(failure):
    service, repository, policy = capability()
    policy.is_allowed.side_effect = failure("dependency failed")
    with pytest.raises(failure):
        service.execute(ACTOR, WORKSPACE, QUERY)
    repository.browse_after.assert_not_called()


@pytest.mark.parametrize("outcome", (PermissionGrantRepositoryError("failed"), 1, None))
def test_repository_permission_policy_reuses_existing_fail_closed_behavior(outcome):
    grants = Mock()
    if isinstance(outcome, Exception):
        grants.is_granted.side_effect = outcome
    else:
        grants.is_granted.return_value = outcome
    repository = Mock(spec=KnowledgeBrowseAfterRepository)
    service = StructuredKnowledgeBrowseAfterCapability(
        repository, RepositoryPermissionPolicy(grants)
    )
    with pytest.raises(LocalPermissionDenied):
        service.execute(ACTOR, WORKSPACE, QUERY)
    repository.browse_after.assert_not_called()


def test_every_execution_reauthorizes_without_inherited_permission():
    service, repository, policy = capability()
    policy.is_allowed.side_effect = (True, False, True)
    service.execute(ACTOR, WORKSPACE, QUERY)
    with pytest.raises(LocalPermissionDenied):
        service.execute(ACTOR, WORKSPACE, QUERY)
    service.execute(ACTOR, WORKSPACE, QUERY)
    assert policy.is_allowed.call_count == 3
    assert repository.browse_after.call_count == 2


@pytest.mark.parametrize(
    "actions", (frozenset(), frozenset({KNOWLEDGE_RECORDS_READ, KNOWLEDGE_RECORDS_ADD}))
)
def test_other_permissions_do_not_authorize(actions):
    grants = (
        (PermissionGrant(ACTOR.actor_id, WORKSPACE.workspace_id, actions),)
        if actions
        else ()
    )
    repository = Mock(spec=KnowledgeBrowseAfterRepository)
    service = StructuredKnowledgeBrowseAfterCapability(
        repository, ExplicitPermissionPolicy(grants)
    )
    with pytest.raises(LocalPermissionDenied):
        service.execute(ACTOR, WORKSPACE, QUERY)
    repository.browse_after.assert_not_called()


def corrupt(field, value):
    row = summary("r")
    object.__setattr__(row, field, value)
    return row


@pytest.mark.parametrize(
    "rows",
    (
        [],
        None,
        (object(),),
        tuple(summary(f"r-{i:03}") for i in range(52)),
        (summary("r"), summary("r")),
        (summary("s"), summary("r")),
        (summary("m"),),
        (summary("a"),),
        (summary("r", OTHER),),
        (corrupt("record_id", " r "),),
        (corrupt("record_id", 1),),
        (corrupt("key", ""),),
        (corrupt("kind", "fact"),),
        (corrupt("workspace", "selected"),),
        tuple(summary(f"r-{i:03}") for i in range(50)) + (summary("a"),),
    ),
)
def test_corrupt_output_is_rejected_without_repair_or_partial_result(rows):
    service, repository, _ = capability(rows)
    with pytest.raises(ValueError):
        service.execute(ACTOR, WORKSPACE, QUERY)
    repository.browse_after.assert_called_once()


@pytest.mark.parametrize(
    "actor,workspace,intent",
    (
        ("actor", WORKSPACE, QUERY),
        (ACTOR, "selected", QUERY),
        (ACTOR, WORKSPACE, BrowseKnowledgeRecordsQuery()),
    ),
)
def test_invalid_context_or_query_never_touches_dependencies(actor, workspace, intent):
    service, repository, policy = capability()
    with pytest.raises((TypeError, ValueError)):
        service.execute(actor, workspace, intent)
    policy.is_allowed.assert_not_called()
    repository.browse_after.assert_not_called()


def test_declared_data_failure_is_sanitized():
    service, repository, _ = capability()
    repository.browse_after.side_effect = LocalRepositoryError("private details")
    with pytest.raises(LocalRepositoryError, match="could not be completed") as caught:
        service.execute(ACTOR, WORKSPACE, QUERY)
    assert "private" not in str(caught.value)


@pytest.fixture
def adapters(tmp_path):
    storage = SQLiteLocalStorage(tmp_path / "continuation.sqlite3")
    storage.open()
    storage.initialize()
    try:
        yield (
            InMemoryKnowledgeRecordRepository(),
            SQLiteKnowledgeRecordRepository(storage),
            storage,
        )
    finally:
        storage.close()


@pytest.mark.parametrize("count", (0, 1, 49, 50, 51, 100, 101))
def test_adapter_bounds_workspace_before_limit_and_no_mutation(adapters, count):
    memory, sqlite, storage = adapters
    ids = tuple(f"r-{i:03}" for i in range(count))
    for repository in (memory, sqlite):
        for i in reversed(range(110)):
            repository.store(record(f"n-{i:03}", OTHER))
            repository.store(record(f"r-{i:03}", OTHER))
        for identifier in reversed(ids):
            repository.store(record(identifier))
        repository.store(record("a"))
    before_memory = dict(memory._records)
    before_sqlite = tuple(storage._connection.iterdump())
    results = [repo.browse_after(WORKSPACE, "m") for repo in (memory, sqlite)]
    assert results[0] == results[1]
    assert tuple(row.record_id for row in results[0]) == ids[:51]
    for repository in (memory, sqlite):
        service = StructuredKnowledgeBrowseAfterCapability(
            repository,
            ExplicitPermissionPolicy(
                (
                    PermissionGrant(
                        ACTOR.actor_id,
                        WORKSPACE.workspace_id,
                        frozenset({KNOWLEDGE_RECORDS_BROWSE}),
                    ),
                )
            ),
        )
        page = service.execute(ACTOR, WORKSPACE, QUERY)
        assert tuple(row.record_id for row in page.records) == ids[:50]
        assert page.truncated is (count > 50)
        assert repository.browse_after(WORKSPACE, "m") == results[0]
    assert memory._records == before_memory
    assert tuple(storage._connection.iterdump()) == before_sqlite
    for row in results[0]:
        assert tuple(field.name for field in fields(row)) == (
            "record_id",
            "workspace",
            "kind",
            "key",
        )
        assert row.workspace == WORKSPACE


@pytest.mark.parametrize(
    "anchor", ("0", "A", "b", "e\u0301", "\u200b", "\ufeff", "\U0001f600", "\U0010ffff")
)
def test_ordinal_binary_unicode_and_absent_anchor_parity(adapters, anchor):
    memory, sqlite, _ = adapters
    ids = (
        "A",
        "a",
        "e\u0301",
        "z",
        "\u00e9",
        "\u200b",
        "\ue000",
        "\ufeff",
        "\U00010000",
        "\U0001f600",
    )
    expected = tuple(identifier for identifier in ids if identifier > anchor)
    for repository in (memory, sqlite):
        for identifier in reversed(ids):
            repository.store(record(identifier))
        assert (
            tuple(row.record_id for row in repository.browse_after(WORKSPACE, anchor))
            == expected
        )
    assert memory.browse_after(WORKSPACE, anchor) == sqlite.browse_after(
        WORKSPACE, anchor
    )


def test_separate_calls_observe_new_rows_without_snapshot_or_representability_filter(
    adapters,
):
    memory, sqlite, _ = adapters
    for repository in (memory, sqlite):
        repository.store(record("z"))
        assert tuple(
            row.record_id for row in repository.browse_after(WORKSPACE, "m")
        ) == ("z",)
        repository.store(record("a-new"))
        repository.store(record("n" * 9000))
        assert tuple(
            row.record_id for row in repository.browse_after(WORKSPACE, "m")
        ) == ("n" * 9000, "z")


def test_sqlite_one_bounded_metadata_select_and_no_writes(adapters):
    _, repository, storage = adapters
    repository.store(record("z"))
    connection = storage._connection
    reads, statements = [], []
    forbidden = {"knowledge_value", "source_type", "source_reference"}

    def authorize(action, table, column, database, trigger):
        if action == sqlite3.SQLITE_READ and table == "knowledge_records":
            reads.append(column)
            if column in forbidden:
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    before = tuple(connection.iterdump())
    changes = connection.total_changes
    connection.set_authorizer(authorize)
    connection.set_trace_callback(statements.append)
    assert repository.browse_after(WORKSPACE, "m") == (summary("z"),)
    # The existing storage guard checks schema version before the one data query.
    assert len(statements) == 2
    assert statements[0] == "PRAGMA user_version"
    sql = statements[1]
    assert "WHERE workspace_id = 'selected' AND record_id COLLATE BINARY > 'm'" in sql
    assert sql.endswith("ORDER BY record_id COLLATE BINARY ASC LIMIT 51")
    assert set(reads) == {"workspace_id", "record_id", "kind", "knowledge_key"}
    for column in forbidden:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(f"SELECT {column} FROM knowledge_records").fetchall()
    connection.set_authorizer(None)
    connection.set_trace_callback(None)
    assert connection.total_changes == changes
    assert tuple(connection.iterdump()) == before


def test_sqlite_failure_retains_existing_error_contract(adapters):
    _, repository, storage = adapters
    storage._connection.execute("DROP TABLE knowledge_records")
    with pytest.raises(LocalStorageError, match="browse-after failed"):
        repository.browse_after(WORKSPACE, "m")
