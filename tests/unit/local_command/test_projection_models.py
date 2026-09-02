"""Focused contract tests for Sprint 35 application list projections."""

from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from app.cognition.local_resolution.models import KnowledgeKind
from app.local_command import (
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    LocalCommandProjectionKind,
    LocalKnowledgeFindProjection,
    LocalKnowledgeProjectionOperation,
    LocalKnowledgeReadProjection,
    LocalKnowledgeRecordKind,
    LocalKnowledgeRecordProjection,
    LocalKnowledgeStoreProjection,
    LocalListAddProjection,
    LocalListProjectionOperation,
    LocalListReadProjection,
    application_error,
)


def _add_projection(**overrides: object) -> LocalListAddProjection:
    values: dict[str, object] = {
        "list_id": "groceries",
        "added": ("milk",),
        "already_present": ("eggs",),
        "items": ("eggs", "milk"),
    }
    values.update(overrides)
    return LocalListAddProjection(**cast(Any, values))


def _read_projection(**overrides: object) -> LocalListReadProjection:
    values: dict[str, object] = {
        "list_id": "groceries",
        "items": ("milk", "eggs"),
    }
    values.update(overrides)
    return LocalListReadProjection(**cast(Any, values))


def test_projection_enums_have_exact_closed_values() -> None:
    assert tuple(LocalCommandProjectionKind) == (
        LocalCommandProjectionKind.LIST,
        LocalCommandProjectionKind.KNOWLEDGE,
    )
    assert LocalCommandProjectionKind.LIST.value == "list"
    assert LocalCommandProjectionKind.KNOWLEDGE.value == "knowledge"
    assert tuple(LocalListProjectionOperation) == (
        LocalListProjectionOperation.ADD,
        LocalListProjectionOperation.READ,
    )
    assert LocalListProjectionOperation.ADD.value == "add"
    assert LocalListProjectionOperation.READ.value == "read"


def test_knowledge_enums_have_exact_closed_values() -> None:
    assert tuple(LocalKnowledgeProjectionOperation) == (
        LocalKnowledgeProjectionOperation.STORE,
        LocalKnowledgeProjectionOperation.READ,
        LocalKnowledgeProjectionOperation.FIND,
    )
    assert tuple(item.value for item in LocalKnowledgeProjectionOperation) == (
        "store",
        "read",
        "find",
    )
    assert tuple(LocalKnowledgeRecordKind) == (
        LocalKnowledgeRecordKind.FACT,
        LocalKnowledgeRecordKind.CONCEPT,
        LocalKnowledgeRecordKind.STATE,
    )
    assert tuple(item.value for item in LocalKnowledgeRecordKind) == (
        "fact",
        "concept",
        "state",
    )


def _record(
    record_id: str = "record-1",
    kind: LocalKnowledgeRecordKind = LocalKnowledgeRecordKind.FACT,
    key: str = "child.diaper_size",
    value: str = "medium",
) -> LocalKnowledgeRecordProjection:
    return LocalKnowledgeRecordProjection(record_id, kind, key, value)


@pytest.mark.parametrize("kind", tuple(LocalKnowledgeRecordKind))
def test_knowledge_record_is_valid_frozen_slotted_and_preserves_strings(
    kind: LocalKnowledgeRecordKind,
) -> None:
    record = _record(" id ", kind, " key ", " value ")

    assert (record.record_id, record.key, record.value) == (
        " id ",
        " key ",
        " value ",
    )
    assert not hasattr(record, "__dict__")
    assert not hasattr(record, "workspace")
    assert not hasattr(record, "provenance")
    with pytest.raises(FrozenInstanceError):
        cast(Any, record).value = "changed"


@pytest.mark.parametrize("field_name", ("record_id", "key", "value"))
@pytest.mark.parametrize("value", ("", "   ", 1, None, True))
def test_knowledge_record_rejects_invalid_text(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {
        "record_id": "record-1",
        "kind": LocalKnowledgeRecordKind.FACT,
        "key": "key",
        "value": "value",
    }
    values[field_name] = value
    with pytest.raises(ValueError, match="Knowledge record"):
        LocalKnowledgeRecordProjection(**cast(Any, values))


@pytest.mark.parametrize("kind", ("fact", KnowledgeKind.FACT, None, True))
def test_knowledge_record_requires_application_owned_exact_kind(
    kind: object,
) -> None:
    with pytest.raises(ValueError, match="kind is invalid"):
        _record(kind=cast(Any, kind))


def test_knowledge_record_has_no_invented_value_length_limit() -> None:
    value = "x" * 8193
    assert _record(value=value).value == value


@pytest.mark.parametrize("created", (True, False))
def test_store_projection_is_fixed_and_valid(created: bool) -> None:
    record = _record()
    projection = LocalKnowledgeStoreProjection(record, created)

    assert projection.record is record
    assert projection.created is created
    assert projection.kind is LocalCommandProjectionKind.KNOWLEDGE
    assert projection.operation is LocalKnowledgeProjectionOperation.STORE
    assert not hasattr(projection, "__dict__")


def test_store_projection_rejects_invalid_inputs_and_discriminators() -> None:
    with pytest.raises(ValueError, match="record is invalid"):
        LocalKnowledgeStoreProjection(cast(Any, object()), True)
    with pytest.raises(ValueError, match="created must be explicit"):
        LocalKnowledgeStoreProjection(_record(), cast(Any, 1))
    with pytest.raises(TypeError):
        LocalKnowledgeStoreProjection(
            _record(), True, kind=LocalCommandProjectionKind.KNOWLEDGE
        )
    with pytest.raises(TypeError):
        LocalKnowledgeStoreProjection(
            _record(), True, operation=LocalKnowledgeProjectionOperation.STORE
        )


def test_read_projection_is_fixed_valid_and_has_no_created_member() -> None:
    record = _record()
    projection = LocalKnowledgeReadProjection(record)

    assert projection.record is record
    assert projection.kind is LocalCommandProjectionKind.KNOWLEDGE
    assert projection.operation is LocalKnowledgeProjectionOperation.READ
    assert not hasattr(projection, "created")
    assert not hasattr(projection, "__dict__")
    with pytest.raises(ValueError, match="record is invalid"):
        LocalKnowledgeReadProjection(cast(Any, object()))
    with pytest.raises(TypeError):
        LocalKnowledgeReadProjection(
            record, operation=LocalKnowledgeProjectionOperation.READ
        )


def _records(count: int) -> tuple[LocalKnowledgeRecordProjection, ...]:
    return tuple(_record(record_id=f"record-{index}") for index in range(count))


@pytest.mark.parametrize(
    ("records", "truncated"),
    (((), False), (_records(1), False), (_records(50), False), (_records(50), True)),
)
def test_find_projection_accepts_valid_boundaries(
    records: tuple[LocalKnowledgeRecordProjection, ...],
    truncated: bool,
) -> None:
    projection = LocalKnowledgeFindProjection(records, truncated)

    assert projection.records is records
    assert projection.truncated is truncated
    assert projection.kind is LocalCommandProjectionKind.KNOWLEDGE
    assert projection.operation is LocalKnowledgeProjectionOperation.FIND
    assert not hasattr(projection, "__dict__")


def test_find_projection_rejects_invalid_shape_and_duplicates() -> None:
    with pytest.raises(ValueError, match="exceed the maximum"):
        LocalKnowledgeFindProjection(_records(51), False)
    with pytest.raises(ValueError, match="require 50"):
        LocalKnowledgeFindProjection(_records(49), True)
    with pytest.raises(ValueError, match="truncated must be explicit"):
        LocalKnowledgeFindProjection((), cast(Any, 0))
    with pytest.raises(ValueError, match="must be a tuple"):
        LocalKnowledgeFindProjection(cast(Any, []), False)
    with pytest.raises(ValueError, match="records are invalid"):
        LocalKnowledgeFindProjection((cast(Any, object()),), False)
    record = _record()
    with pytest.raises(ValueError, match="must be unique"):
        LocalKnowledgeFindProjection((record, record), False)
    with pytest.raises(TypeError):
        LocalKnowledgeFindProjection(
            (), False, operation=LocalKnowledgeProjectionOperation.FIND
        )


def test_find_projection_preserves_input_order() -> None:
    records = (_record("second"), _record("first"))
    assert LocalKnowledgeFindProjection(records, False).records == records


def test_add_projection_is_valid_normalized_frozen_and_discriminated() -> None:
    projection = _add_projection(list_id="  groceries  ")

    assert projection.list_id == "groceries"
    assert projection.added == ("milk",)
    assert projection.already_present == ("eggs",)
    assert projection.items == ("eggs", "milk")
    assert projection.kind is LocalCommandProjectionKind.LIST
    assert projection.operation is LocalListProjectionOperation.ADD

    with pytest.raises(FrozenInstanceError):
        cast(Any, projection).items = ()


def test_add_projection_discriminators_are_not_caller_selectable() -> None:
    with pytest.raises(TypeError):
        _add_projection(kind=LocalCommandProjectionKind.LIST)
    with pytest.raises(TypeError):
        _add_projection(operation=LocalListProjectionOperation.READ)


@pytest.mark.parametrize("list_id", ("", "   ", 1, None, True))
def test_add_projection_rejects_invalid_list_id(list_id: object) -> None:
    with pytest.raises(ValueError, match="list ID"):
        _add_projection(list_id=list_id)


@pytest.mark.parametrize("field_name", ("added", "already_present", "items"))
@pytest.mark.parametrize("value", ([], ["milk"], "milk", None))
def test_add_projection_requires_exact_tuples(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError, match="tuple"):
        _add_projection(**{field_name: value})


@pytest.mark.parametrize("field_name", ("added", "already_present", "items"))
@pytest.mark.parametrize("member", ("", "   ", 1, None, True))
def test_add_projection_rejects_invalid_tuple_members(
    field_name: str,
    member: object,
) -> None:
    with pytest.raises(ValueError, match="non-empty strings"):
        _add_projection(**{field_name: (member,)})


def test_add_projection_allows_empty_structural_tuples() -> None:
    projection = _add_projection(added=(), already_present=(), items=())

    assert projection.added == ()
    assert projection.already_present == ()
    assert projection.items == ()


def test_read_projection_is_valid_normalized_frozen_and_discriminated() -> None:
    projection = _read_projection(list_id="  groceries  ", items=())

    assert projection.list_id == "groceries"
    assert projection.items == ()
    assert projection.kind is LocalCommandProjectionKind.LIST
    assert projection.operation is LocalListProjectionOperation.READ

    with pytest.raises(FrozenInstanceError):
        cast(Any, projection).list_id = "other"


def test_read_projection_discriminators_are_not_caller_selectable() -> None:
    with pytest.raises(TypeError):
        _read_projection(kind=LocalCommandProjectionKind.LIST)
    with pytest.raises(TypeError):
        _read_projection(operation=LocalListProjectionOperation.ADD)


@pytest.mark.parametrize("list_id", ("", "   ", 1, None, True))
def test_read_projection_rejects_invalid_list_id(list_id: object) -> None:
    with pytest.raises(ValueError, match="list ID"):
        _read_projection(list_id=list_id)


@pytest.mark.parametrize("value", ([], ["milk"], "milk", None))
def test_read_projection_requires_exact_items_tuple(value: object) -> None:
    with pytest.raises(ValueError, match="tuple"):
        _read_projection(items=value)


@pytest.mark.parametrize("member", ("", "   ", 1, None, True))
def test_read_projection_rejects_invalid_item(member: object) -> None:
    with pytest.raises(ValueError, match="non-empty strings"):
        _read_projection(items=(member,))


@pytest.mark.parametrize(
    "projection",
    (
        _add_projection(),
        _read_projection(),
        LocalKnowledgeStoreProjection(_record(), True),
        LocalKnowledgeReadProjection(_record()),
        LocalKnowledgeFindProjection((_record(),), False),
    ),
)
def test_successful_local_result_allows_closed_projection(projection: object) -> None:
    result = LocalCommandApplicationResult(
        True,
        route=LocalCommandApplicationRoute.LOCAL,
        response="completed",
        projection=cast(Any, projection),
    )

    assert result.projection is projection


def test_successful_local_result_allows_projection_none() -> None:
    result = LocalCommandApplicationResult(
        True,
        route=LocalCommandApplicationRoute.LOCAL,
        response="Knowledge record stored locally.",
    )

    assert result.projection is None


@pytest.mark.parametrize(
    ("success", "route", "response", "error"),
    (
        (
            False,
            LocalCommandApplicationRoute.LOCAL,
            None,
            application_error(
                LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED
            ),
        ),
        (True, None, "completed", None),
        (True, LocalCommandApplicationRoute.COGNITIVE, "completed", None),
        (True, LocalCommandApplicationRoute.SAFE_INSUFFICIENCY, "completed", None),
    ),
)
def test_projection_requires_successful_local_route(
    success: bool,
    route: LocalCommandApplicationRoute | None,
    response: str | None,
    error: object,
) -> None:
    with pytest.raises(ValueError, match="projection requires local success"):
        LocalCommandApplicationResult(
            success,
            route=route,
            response=response,
            error=cast(Any, error),
            projection=_read_projection(),
        )


def test_application_result_rejects_unknown_projection_type() -> None:
    with pytest.raises(ValueError, match="projection is invalid"):
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="completed",
            projection=cast(Any, object()),
        )


def test_historical_result_construction_remains_valid() -> None:
    local = LocalCommandApplicationResult(
        True,
        route=LocalCommandApplicationRoute.LOCAL,
        response="local",
    )
    cognitive = LocalCommandApplicationResult(
        True,
        route=LocalCommandApplicationRoute.COGNITIVE,
        response="cognitive",
    )
    failure = LocalCommandApplicationResult(
        False,
        error=application_error(LocalCommandApplicationErrorCode.ACCESS_DENIED),
    )

    assert local.projection is None
    assert cognitive.projection is None
    assert failure.projection is None
