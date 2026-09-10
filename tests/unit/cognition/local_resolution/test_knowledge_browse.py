"""Bounded metadata exploration, shared by memory and SQLite adapters."""

import inspect
from dataclasses import FrozenInstanceError, fields
from unittest.mock import Mock

import pytest

from app.cognition.local_resolution.capability import LocalPermissionDenied
from app.cognition.local_resolution.contracts import (
    KnowledgeBrowseRepository,
    KnowledgeRecordRepository,
    LocalRepositoryError,
    PermissionGrantRepositoryError,
)
from app.cognition.local_resolution.knowledge_browse_capability import (
    StructuredKnowledgeBrowseCapability,
)
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    BrowseKnowledgeRecordsQuery,
    KnowledgeBrowseResolutionResult,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeRecordsBrowsed,
    KnowledgeRecordSummary,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_BROWSE,
    KNOWLEDGE_RECORDS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
    RepositoryPermissionPolicy,
)
from app.cognition.local_resolution.repository import InMemoryKnowledgeRecordRepository
from app.cognition.local_resolution.resolver import LocalFirstResolver
from app.infrastructure.local_storage.sqlite_storage import (
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
)


@pytest.fixture(params=("memory", "sqlite"))
def repository(request, tmp_path):
    if request.param == "memory":
        yield InMemoryKnowledgeRecordRepository()
        return
    storage = SQLiteLocalStorage(tmp_path / "browse.sqlite3")
    try:
        storage.open()
        storage.initialize()
        yield SQLiteKnowledgeRecordRepository(storage)
    finally:
        storage.close()


def test_models_are_closed_immutable_and_protocol_is_separate():
    query = BrowseKnowledgeRecordsQuery()
    assert fields(query) == ()
    with pytest.raises(TypeError):
        BrowseKnowledgeRecordsQuery(key="x")
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        query.key = "x"
    summary = KnowledgeRecordSummary(
        "id", WorkspaceIdentity("w"), KnowledgeKind.FACT, "k"
    )
    assert tuple(field.name for field in fields(summary)) == (
        "record_id",
        "workspace",
        "kind",
        "key",
    )
    for field in fields(summary):
        with pytest.raises(FrozenInstanceError):
            setattr(summary, field.name, None)
    assert not hasattr(summary, "__dict__")
    assert tuple(inspect.signature(KnowledgeBrowseRepository.browse).parameters) == (
        "self",
        "workspace",
    )
    assert {
        name for name in vars(KnowledgeRecordRepository) if not name.startswith("_")
    } == {
        "store",
        "read",
        "find_by_key",
    }


@pytest.mark.parametrize("field", ("record_id", "key"))
@pytest.mark.parametrize(
    "value",
    (
        None,
        1,
        False,
        "",
        " ",
        " x",
        "x ",
        "\tx",
        "x\n",
        "\u001cx",
        "x\u00a0",
        "\u3000x",
    ),
)
def test_summary_rejects_invalid_or_untrimmed_text(field, value):
    arguments = dict(
        record_id="id",
        workspace=WorkspaceIdentity("w"),
        kind=KnowledgeKind.FACT,
        key="k",
    )
    arguments[field] = value
    with pytest.raises(ValueError):
        KnowledgeRecordSummary(**arguments)


@pytest.mark.parametrize(
    "field,value",
    (("workspace", "w"), ("workspace", None), ("kind", "fact"), ("kind", None)),
)
def test_summary_rejects_invalid_scope_and_kind(field, value):
    arguments = dict(
        record_id="id",
        workspace=WorkspaceIdentity("w"),
        kind=KnowledgeKind.FACT,
        key="k",
    )
    arguments[field] = value
    with pytest.raises(ValueError):
        KnowledgeRecordSummary(**arguments)


def test_summary_preserves_literal_unicode_without_normalization():
    literal = "<b>É e\u0301  😀\tZ</b>"
    summary = KnowledgeRecordSummary(
        literal, WorkspaceIdentity("w"), KnowledgeKind.STATE, literal
    )
    assert summary.record_id == literal
    assert summary.key == literal


@pytest.mark.parametrize("total", (0, 49, 50, 51, 67))
def test_browse_boundaries_isolation_and_literal_order(repository, total):
    workspace, other = WorkspaceIdentity("selected"), WorkspaceIdentity("other")
    ids = tuple(f"r-{number:03}" for number in range(total))
    key = "<key>É e\u0301 😀</key>"
    for number in reversed(range(75)):
        repository.store(
            KnowledgeRecord(
                f"a-{number:03}",
                other,
                KnowledgeKind.FACT,
                "other",
                "secret",
                KnowledgeProvenance("test", "other"),
            )
        )
    for number, record_id in enumerate(reversed(ids)):
        repository.store(
            KnowledgeRecord(
                record_id,
                other,
                KnowledgeKind.FACT,
                "other",
                "secret",
                KnowledgeProvenance("test", "other"),
            )
        )
        repository.store(
            KnowledgeRecord(
                record_id,
                workspace,
                tuple(KnowledgeKind)[number % 3],
                key,
                "<value>😀</value>",
                KnowledgeProvenance("test", "private"),
            )
        )
    result = repository.browse(workspace)
    assert type(result) is tuple
    assert tuple(row.record_id for row in result) == ids[:51]
    assert len(result) == min(total, 51)
    assert len({row.record_id for row in result}) == len(result)
    assert all(row.workspace == workspace and row.key == key for row in result)
    assert repository.browse(workspace) == result
    assert repository.browse(WorkspaceIdentity("empty")) == ()


def test_browse_unicode_order_including_supplementary_characters(repository):
    workspace = WorkspaceIdentity("w")
    ids = ("A", "a", "e\u0301", "z", "é", "\ue000", "\U00010000", "😀")
    for record_id in reversed(ids):
        repository.store(
            KnowledgeRecord(
                record_id,
                workspace,
                KnowledgeKind.CONCEPT,
                "same",
                "value",
                KnowledgeProvenance("test", "source"),
            )
        )
    assert tuple(row.record_id for row in repository.browse(workspace)) == ids


@pytest.mark.parametrize("workspace", (None, "w", 1))
def test_browse_rejects_invalid_workspace(repository, workspace):
    with pytest.raises(ValueError, match="workspace"):
        repository.browse(workspace)


def _summaries(total, workspace=None):
    workspace = workspace or WorkspaceIdentity("selected")
    return tuple(
        KnowledgeRecordSummary(f"r-{i:03}", workspace, KnowledgeKind.FACT, "same key")
        for i in range(total)
    )


@pytest.mark.parametrize("total", (0, 49, 50, 51))
def test_capability_authorizes_then_browses_exact_workspace_once(total):
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("selected")
    records = _summaries(total, workspace)
    calls = []
    policy = Mock()
    repository = Mock(spec=KnowledgeBrowseRepository)

    def authorize(got_actor, got_workspace, action):
        assert got_actor is actor and got_workspace is workspace
        assert action == "knowledge.records.browse"
        calls.append("permission")
        return True

    def browse(got_workspace):
        assert got_workspace is workspace
        calls.append("browse")
        return records

    policy.is_allowed.side_effect = authorize
    repository.browse.side_effect = browse
    result = StructuredKnowledgeBrowseCapability(repository, policy).execute(
        actor, workspace, BrowseKnowledgeRecordsQuery()
    )
    assert calls == ["permission", "browse"]
    policy.is_allowed.assert_called_once_with(
        actor, workspace, KNOWLEDGE_RECORDS_BROWSE
    )
    repository.browse.assert_called_once_with(workspace)
    assert type(result) is KnowledgeRecordsBrowsed
    assert result.records == records[:50]
    assert all(actual is original for actual, original in zip(result.records, records))
    assert result.truncated is (total == 51)


@pytest.mark.parametrize(
    "actions",
    (
        (),
        (KNOWLEDGE_RECORDS_READ,),
        (KNOWLEDGE_RECORDS_BROWSE,),
        (KNOWLEDGE_RECORDS_READ, KNOWLEDGE_RECORDS_BROWSE),
    ),
)
def test_browse_requires_its_own_permission(actions):
    actor, workspace = ActorIdentity("actor"), WorkspaceIdentity("selected")
    grants = (
        (PermissionGrant("actor", "selected", frozenset(actions)),) if actions else ()
    )
    repository = Mock(spec=KnowledgeBrowseRepository)
    repository.browse.return_value = ()
    capability = StructuredKnowledgeBrowseCapability(
        repository, ExplicitPermissionPolicy(grants)
    )
    if KNOWLEDGE_RECORDS_BROWSE in actions:
        assert (
            capability.execute(actor, workspace, BrowseKnowledgeRecordsQuery()).records
            == ()
        )
        repository.browse.assert_called_once_with(workspace)
    else:
        with pytest.raises(LocalPermissionDenied, match="not authorized"):
            capability.execute(actor, workspace, BrowseKnowledgeRecordsQuery())
        repository.browse.assert_not_called()


@pytest.mark.parametrize("allowed", (False, None, 0, 1, "true", (), []))
def test_invalid_or_denied_permission_never_queries_knowledge(allowed):
    repository, policy = Mock(spec=KnowledgeBrowseRepository), Mock()
    policy.is_allowed.return_value = allowed
    with pytest.raises(LocalPermissionDenied):
        StructuredKnowledgeBrowseCapability(repository, policy).execute(
            ActorIdentity("actor"),
            WorkspaceIdentity("selected"),
            BrowseKnowledgeRecordsQuery(),
        )
    repository.browse.assert_not_called()


@pytest.mark.parametrize(
    "actor,workspace,intent",
    (
        (None, WorkspaceIdentity("w"), BrowseKnowledgeRecordsQuery()),
        ("actor", WorkspaceIdentity("w"), BrowseKnowledgeRecordsQuery()),
        (ActorIdentity("a"), None, BrowseKnowledgeRecordsQuery()),
        (ActorIdentity("a"), "w", BrowseKnowledgeRecordsQuery()),
        (ActorIdentity("a"), WorkspaceIdentity("w"), object()),
    ),
)
def test_invalid_capability_inputs_skip_permission_and_knowledge(
    actor, workspace, intent
):
    repository, policy = Mock(spec=KnowledgeBrowseRepository), Mock()
    with pytest.raises((TypeError, ValueError)):
        StructuredKnowledgeBrowseCapability(repository, policy).execute(
            actor, workspace, intent
        )
    policy.is_allowed.assert_not_called()
    repository.browse.assert_not_called()


def _corrupt_summary(field, value):
    summary = _summaries(1)[0]
    object.__setattr__(summary, field, value)
    return summary


@pytest.mark.parametrize(
    "records",
    (
        None,
        False,
        [],
        {},
        "secret",
        (object(),),
        _summaries(1, WorkspaceIdentity("other")),
        (_summaries(1)[0], _summaries(1)[0]),
        tuple(reversed(_summaries(2))),
        _summaries(52),
        (_corrupt_summary("record_id", " id "),),
        (_corrupt_summary("key", None),),
        (_corrupt_summary("kind", "fact"),),
        (_corrupt_summary("workspace", "selected"),),
        # The lookahead must be validated too, not discarded before checking.
        _summaries(50) + (_summaries(1, WorkspaceIdentity("other"))[0],),
        _summaries(50) + (_summaries(1)[0],),
    ),
)
def test_capability_rejects_corrupt_return_without_repair_or_partial_result(records):
    repository, policy = Mock(spec=KnowledgeBrowseRepository), Mock()
    policy.is_allowed.return_value = True
    repository.browse.return_value = records
    with pytest.raises(ValueError) as error:
        StructuredKnowledgeBrowseCapability(repository, policy).execute(
            ActorIdentity("actor"),
            WorkspaceIdentity("selected"),
            BrowseKnowledgeRecordsQuery(),
        )
    assert "secret" not in str(error.value)
    repository.browse.assert_called_once()
    assert repository.browse.return_value is records


def test_declared_repository_failure_is_sanitized_without_a_result():
    repository, policy = Mock(spec=KnowledgeBrowseRepository), Mock()
    policy.is_allowed.return_value = True
    repository.browse.side_effect = LocalRepositoryError("private database details")
    with pytest.raises(LocalRepositoryError) as error:
        StructuredKnowledgeBrowseCapability(repository, policy).execute(
            ActorIdentity("actor"),
            WorkspaceIdentity("selected"),
            BrowseKnowledgeRecordsQuery(),
        )
    assert str(error.value) == "Local knowledge browse could not be completed."
    assert error.value.__suppress_context__
    repository.browse.assert_called_once()


def test_permission_repository_failure_retains_existing_fail_closed_policy():
    grants, repository = Mock(), Mock(spec=KnowledgeBrowseRepository)
    grants.is_granted.side_effect = PermissionGrantRepositoryError("private details")
    with pytest.raises(LocalPermissionDenied):
        StructuredKnowledgeBrowseCapability(
            repository, RepositoryPermissionPolicy(grants)
        ).execute(
            ActorIdentity("actor"),
            WorkspaceIdentity("selected"),
            BrowseKnowledgeRecordsQuery(),
        )
    grants.is_granted.assert_called_once()
    repository.browse.assert_not_called()


@pytest.mark.parametrize("boundary", ("permission", "repository"))
def test_unexpected_errors_are_not_converted_to_local_results(boundary):
    repository, policy = Mock(spec=KnowledgeBrowseRepository), Mock()
    failure = RuntimeError("unexpected programming failure")
    policy.is_allowed.return_value = True
    if boundary == "permission":
        policy.is_allowed.side_effect = failure
    else:
        repository.browse.side_effect = failure
    with pytest.raises(RuntimeError) as error:
        StructuredKnowledgeBrowseCapability(repository, policy).execute(
            ActorIdentity("actor"),
            WorkspaceIdentity("selected"),
            BrowseKnowledgeRecordsQuery(),
        )
    assert error.value is failure
    assert repository.browse.call_count == (boundary == "repository")


@pytest.mark.parametrize(
    "total,truncated", ((0, False), (49, False), (50, False), (50, True))
)
def test_browse_results_are_immutable_and_admit_empty_success(total, truncated):
    records = _summaries(total)
    results = (
        KnowledgeRecordsBrowsed(records, truncated),
        KnowledgeBrowseResolutionResult(
            True,
            True,
            "Knowledge browsed locally.",
            LOCAL_CAPABILITY_ROUTE,
            records,
            truncated,
        ),
        KnowledgeBrowseResolutionResult(
            True,
            False,
            "Local browse denied.",
            LOCAL_CAPABILITY_ROUTE,
            error_code=LOCAL_PERMISSION_DENIED,
        ),
        KnowledgeBrowseResolutionResult(
            True,
            False,
            "Local browse failed.",
            LOCAL_CAPABILITY_ROUTE,
            error_code=LOCAL_VALIDATION_FAILED,
        ),
    )
    for result in results:
        assert not hasattr(result, "__dict__")
        for field in fields(result):
            with pytest.raises(FrozenInstanceError):
                setattr(result, field.name, None)


@pytest.mark.parametrize(
    "records,truncated",
    (
        ([], False),
        ((object(),), False),
        (_summaries(51), False),
        ((), True),
        (_summaries(49), True),
        ((), 0),
        ((), 1),
        ((), None),
        ((), "false"),
        (tuple(reversed(_summaries(2))), False),
        ((_summaries(1)[0], _summaries(1)[0]), False),
        ((_summaries(1)[0], _summaries(2, WorkspaceIdentity("other"))[1]), False),
    ),
)
def test_both_result_models_reject_invalid_summaries_and_truncation(records, truncated):
    with pytest.raises(ValueError):
        KnowledgeRecordsBrowsed(records, truncated)
    with pytest.raises(ValueError):
        KnowledgeBrowseResolutionResult(
            True, True, "Browse complete.", LOCAL_CAPABILITY_ROUTE, records, truncated
        )


@pytest.mark.parametrize(
    "overrides",
    (
        {"handled": False},
        {"resolution_route": "not_handled"},
        {"model_used": True},
        {"external_access": True},
        {"error_code": LOCAL_VALIDATION_FAILED},
        {"success": False},
        {"success": False, "error_code": "unknown"},
        {
            "success": False,
            "error_code": LOCAL_VALIDATION_FAILED,
            "records": _summaries(1),
        },
        {
            "success": False,
            "error_code": LOCAL_PERMISSION_DENIED,
            "records": _summaries(50),
            "truncated": True,
        },
        {"response": None},
    ),
)
def test_resolution_result_rejects_incoherent_local_outcomes(overrides):
    arguments = dict(
        handled=True,
        success=True,
        response="Done",
        resolution_route=LOCAL_CAPABILITY_ROUTE,
    )
    arguments.update(overrides)
    with pytest.raises(ValueError):
        KnowledgeBrowseResolutionResult(**arguments)


@pytest.mark.parametrize(
    "flag", ("handled", "success", "truncated", "model_used", "external_access")
)
@pytest.mark.parametrize("value", (0, 1, None, "false"))
def test_resolution_result_requires_actual_boolean_flags(flag, value):
    arguments = dict(
        handled=True,
        success=True,
        response="Done",
        resolution_route=LOCAL_CAPABILITY_ROUTE,
    )
    arguments[flag] = value
    with pytest.raises(ValueError):
        KnowledgeBrowseResolutionResult(**arguments)


@pytest.mark.parametrize(
    "scenario,error",
    (
        ("empty", None),
        ("success", None),
        ("denied", LOCAL_PERMISSION_DENIED),
        ("missing", LOCAL_VALIDATION_FAILED),
        ("corrupt", LOCAL_VALIDATION_FAILED),
        ("storage", LOCAL_VALIDATION_FAILED),
        ("identity", LOCAL_VALIDATION_FAILED),
    ),
)
def test_resolver_browse_outcomes_are_local_and_sanitized(scenario, error):
    repository, policy = Mock(spec=KnowledgeBrowseRepository), Mock()
    policy.is_allowed.return_value = scenario != "denied"
    repository.browse.return_value = _summaries(1) if scenario == "success" else ()
    if scenario == "corrupt":
        repository.browse.return_value = _summaries(50) + (_summaries(1)[0],)
    if scenario == "storage":
        repository.browse.side_effect = LocalRepositoryError(
            "private-value provenance workspace"
        )
    capability = StructuredKnowledgeBrowseCapability(repository, policy)
    resolver = LocalFirstResolver(
        Mock(),
        knowledge_browse_capability=(None if scenario == "missing" else capability),
    )
    result = resolver.resolve(
        None if scenario == "identity" else ActorIdentity("actor"),
        WorkspaceIdentity("selected"),
        BrowseKnowledgeRecordsQuery(),
    )
    assert type(result) is KnowledgeBrowseResolutionResult
    assert result.handled is True and result.resolution_route == LOCAL_CAPABILITY_ROUTE
    assert result.success is (error is None) and result.error_code == error
    assert result.model_used is False and result.external_access is False
    assert "workspace" not in result.response and "provenance" not in result.response
    assert "private-value" not in result.response
    assert result.truncated is False
    assert len(result.records) == (scenario == "success")
    assert repository.browse.call_count == (
        scenario not in ("denied", "missing", "identity")
    )


@pytest.mark.parametrize("corruption", ("type", "scope", "boolean"))
def test_resolver_revalidates_injected_capability_results(corruption):
    capability = Mock()
    result = KnowledgeRecordsBrowsed(_summaries(1), False)
    if corruption == "type":
        result = object()
    elif corruption == "scope":
        result = KnowledgeRecordsBrowsed(
            _summaries(1, WorkspaceIdentity("other")), False
        )
    else:
        object.__setattr__(result, "truncated", 0)
    capability.execute.return_value = result
    outcome = LocalFirstResolver(
        Mock(), knowledge_browse_capability=capability
    ).resolve(
        ActorIdentity("actor"),
        WorkspaceIdentity("selected"),
        BrowseKnowledgeRecordsQuery(),
    )
    assert outcome.error_code == LOCAL_VALIDATION_FAILED
    assert outcome.records == () and outcome.truncated is False


def test_resolver_preserves_unexpected_browse_error():
    capability = Mock()
    failure = RuntimeError("unexpected")
    capability.execute.side_effect = failure
    with pytest.raises(RuntimeError) as captured:
        LocalFirstResolver(Mock(), knowledge_browse_capability=capability).resolve(
            ActorIdentity("actor"),
            WorkspaceIdentity("selected"),
            BrowseKnowledgeRecordsQuery(),
        )
    assert captured.value is failure
