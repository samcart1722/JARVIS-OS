"""Focused contract tests for Sprint 35 application list projections."""

from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from app.local_command import (
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    LocalCommandProjectionKind,
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
    assert tuple(LocalCommandProjectionKind) == (LocalCommandProjectionKind.LIST,)
    assert LocalCommandProjectionKind.LIST.value == "list"
    assert tuple(LocalListProjectionOperation) == (
        LocalListProjectionOperation.ADD,
        LocalListProjectionOperation.READ,
    )
    assert LocalListProjectionOperation.ADD.value == "add"
    assert LocalListProjectionOperation.READ.value == "read"


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


@pytest.mark.parametrize("projection", (_add_projection(), _read_projection()))
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
