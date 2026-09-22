"""Transport-boundary tests for authenticated local commands."""
import asyncio
import json
from typing import Any, cast

import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from app.api.models.local_command import (
    LocalCommandHttpError,
    LocalCommandHttpKnowledgeFindProjection,
    LocalCommandHttpKnowledgeReadProjection,
    LocalCommandHttpKnowledgeRecord,
    LocalCommandHttpKnowledgeStoreProjection,
    LocalCommandHttpListAddProjection,
    LocalCommandHttpListReadProjection,
    LocalCommandHttpRequest,
    LocalCommandHttpResponse,
)
from app.api.router import api_router
from app.api.routes import local_command
from app.local_command import (
    LOCAL_COMMAND_TEXT_MAX_LENGTH,
    WORKSPACE_ID_MAX_LENGTH,
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationRequest,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    LocalKnowledgeFindProjection,
    LocalKnowledgeReadProjection,
    LocalKnowledgeRecordKind,
    LocalKnowledgeRecordProjection,
    LocalKnowledgeStoreProjection,
    LocalListAddProjection,
    LocalListReadProjection,
    application_error,
)


def _payload(**overrides) -> dict[str, object]:
    values: dict[str, object] = {
        "proof": "transport-secret-proof",
        "requested_workspace_id": "workspace",
        "text": "list read groceries",
        "allow_cognitive_fallback": False,
    }
    values.update(overrides)
    return values



def _require_http_payload(
    payload: dict[str, object] | str,
) -> dict[str, object]:
    assert isinstance(payload, dict)
    return payload


def _http_error_code(
    payload: dict[str, object] | str,
) -> object:
    error = _require_http_payload(payload).get("error")
    assert isinstance(error, dict)
    return error.get("code")


def _application_error_message(
    result: LocalCommandApplicationResult,
) -> str:
    assert result.error is not None
    return result.error.message

def test_http_request_accepts_strict_valid_transport_input() -> None:
    request = LocalCommandHttpRequest.model_validate(
        _payload(
            requested_workspace_id="  workspace  ",
            text="  list read groceries  ",
            allow_cognitive_fallback=True,
        )
    )

    assert request.proof.get_secret_value() == "transport-secret-proof"
    assert request.requested_workspace_id == "workspace"
    assert request.text == "  list read groceries  "
    assert request.allow_cognitive_fallback is True


def test_http_request_repr_redacts_proof() -> None:
    proof = "proof-that-must-never-appear"
    request = LocalCommandHttpRequest.model_validate(
        _payload(proof=proof)
    )

    representation = repr(request)

    assert proof not in representation
    assert "**********" in representation


def test_http_request_json_serialization_redacts_proof() -> None:
    proof = "proof-that-must-never-serialize"
    request = LocalCommandHttpRequest.model_validate(
        _payload(proof=proof)
    )

    serialized = request.model_dump_json()

    assert proof not in serialized
    assert "**********" in serialized


def test_http_request_python_dump_does_not_contain_raw_proof() -> None:
    proof = "proof-that-must-never-dump"
    request = LocalCommandHttpRequest.model_validate(
        _payload(proof=proof)
    )

    dumped = request.model_dump()

    assert proof not in repr(dumped)
    assert str(dumped["proof"]) == "**********"


@pytest.mark.parametrize(
    "proof",
    (
        None,
        "",
        "   ",
        123,
        True,
    ),
)
def test_http_request_rejects_invalid_proof(proof) -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(proof=proof)
        )


@pytest.mark.parametrize(
    "workspace_id",
    (
        "",
        "   ",
        123,
        True,
        None,
    ),
)
def test_http_request_rejects_invalid_workspace(workspace_id) -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(requested_workspace_id=workspace_id)
        )


def test_http_request_rejects_oversized_workspace() -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(
                requested_workspace_id=(
                    "w" * (WORKSPACE_ID_MAX_LENGTH + 1)
                )
            )
        )


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        123,
        True,
        None,
    ),
)
def test_http_request_rejects_invalid_text(text) -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(text=text)
        )


def test_http_request_rejects_oversized_text() -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(
                text="x" * (LOCAL_COMMAND_TEXT_MAX_LENGTH + 1)
            )
        )


@pytest.mark.parametrize(
    "fallback",
    (
        0,
        1,
        "false",
        "true",
        None,
    ),
)
def test_http_request_requires_strict_boolean_fallback(fallback) -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(allow_cognitive_fallback=fallback)
        )


def test_http_request_requires_explicit_fallback_field() -> None:
    payload = _payload()
    del payload["allow_cognitive_fallback"]

    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(payload)


def test_http_request_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(unexpected="forbidden")
        )


def test_validation_error_does_not_expose_valid_proof() -> None:
    proof = "proof-that-must-survive-validation-safely"

    with pytest.raises(ValidationError) as exc_info:
        LocalCommandHttpRequest.model_validate(
            _payload(
                proof=proof,
                allow_cognitive_fallback="not-a-boolean",
            )
        )

    rendered = (
        str(exc_info.value)
        + repr(exc_info.value)
        + json.dumps(
            exc_info.value.errors(),
            default=str,
        )
    )

    assert proof not in rendered


def test_http_response_has_closed_expected_shape() -> None:
    response = LocalCommandHttpResponse(
        success=False,
        route=None,
        response=None,
        error=LocalCommandHttpError(
            code="access_denied",
            message="Access denied.",
        ),
    )

    assert response.model_dump() == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "access_denied",
            "message": "Access denied.",
        },
        "projection": None,
    }


def test_http_add_projection_model_has_closed_exact_contract() -> None:
    projection = LocalCommandHttpListAddProjection(
        list_id="groceries",
        added=("milk",),
        already_present=("eggs",),
        items=("eggs", "milk"),
    )

    assert projection.model_dump() == {
        "kind": "list",
        "operation": "add",
        "list_id": "groceries",
        "added": ("milk",),
        "already_present": ("eggs",),
        "items": ("eggs", "milk"),
    }


@pytest.mark.parametrize(
    "overrides",
    (
        {"kind": "knowledge"},
        {"operation": "read"},
        {"unexpected": "forbidden"},
    ),
)
def test_http_add_projection_model_rejects_invalid_contract(overrides) -> None:
    values = {
        "list_id": "groceries",
        "added": ("milk",),
        "already_present": (),
        "items": ("milk",),
    }
    values.update(overrides)

    with pytest.raises(ValidationError):
        LocalCommandHttpListAddProjection.model_validate(values)


def test_http_read_projection_model_has_closed_exact_contract() -> None:
    projection = LocalCommandHttpListReadProjection(
        list_id="groceries",
        items=(),
    )

    assert projection.model_dump() == {
        "kind": "list",
        "operation": "read",
        "list_id": "groceries",
        "items": (),
    }


@pytest.mark.parametrize(
    "overrides",
    (
        {"kind": "knowledge"},
        {"operation": "add"},
        {"unexpected": "forbidden"},
    ),
)
def test_http_read_projection_model_rejects_invalid_contract(overrides) -> None:
    values = {
        "list_id": "groceries",
        "items": (),
    }
    values.update(overrides)

    with pytest.raises(ValidationError):
        LocalCommandHttpListReadProjection.model_validate(values)


@pytest.mark.parametrize(
    ("projection", "expected_type"),
    (
        (
            {
                "kind": "list",
                "operation": "add",
                "list_id": "groceries",
                "added": ["milk"],
                "already_present": [],
                "items": ["milk"],
            },
            LocalCommandHttpListAddProjection,
        ),
        (
            {
                "kind": "list",
                "operation": "read",
                "list_id": "groceries",
                "items": [],
            },
            LocalCommandHttpListReadProjection,
        ),
    ),
)
def test_http_projection_union_selects_operation_variant(
    projection,
    expected_type,
) -> None:
    response = LocalCommandHttpResponse(
        success=True,
        route="local",
        response="completed",
        error=None,
        projection=projection,
    )

    assert type(response.projection) is expected_type


def test_http_projection_union_rejects_unknown_operation() -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpResponse(
            success=True,
            route="local",
            response="completed",
            error=None,
            projection=cast(
                Any,
                {
                    "kind": "list",
                    "operation": "delete",
                    "list_id": "groceries",
                    "items": [],
                },
            ),
        )


@pytest.mark.parametrize("kind", ("fact", "concept", "state"))
def test_http_knowledge_record_has_strict_closed_contract(kind) -> None:
    record = LocalCommandHttpKnowledgeRecord(
        record_id="record",
        kind=kind,
        key="key",
        value="value",
    )

    assert record.model_dump() == {
        "record_id": "record",
        "kind": kind,
        "key": "key",
        "value": "value",
    }
    assert not hasattr(record, "workspace")
    assert not hasattr(record, "provenance")


@pytest.mark.parametrize(
    "overrides",
    (
        {"record_id": 1},
        {"key": True},
        {"value": None},
        {"kind": "unknown"},
        {"workspace": "forbidden"},
        {"provenance": "forbidden"},
    ),
)
def test_http_knowledge_record_rejects_invalid_contract(overrides) -> None:
    values = {
        "record_id": "record",
        "kind": "fact",
        "key": "key",
        "value": "value",
    }
    values.update(overrides)
    with pytest.raises(ValidationError):
        LocalCommandHttpKnowledgeRecord.model_validate(values)


def _http_record(**overrides) -> LocalCommandHttpKnowledgeRecord:
    values = {
        "record_id": "record",
        "kind": "fact",
        "key": "key",
        "value": "value",
    }
    values.update(overrides)
    return LocalCommandHttpKnowledgeRecord.model_validate(values)


@pytest.mark.parametrize("created", (True, False))
def test_http_store_projection_has_exact_contract(created) -> None:
    projection = LocalCommandHttpKnowledgeStoreProjection(
        record=_http_record(), created=created
    )
    assert projection.model_dump() == {
        "kind": "knowledge",
        "operation": "store",
        "record": _http_record().model_dump(),
        "created": created,
    }


@pytest.mark.parametrize(
    "model,values,overrides",
    (
        (
            LocalCommandHttpKnowledgeStoreProjection,
            {"record": _http_record(), "created": True},
            ({"created": 1}, {"kind": "list"}, {"operation": "read"}, {"x": 1}),
        ),
        (
            LocalCommandHttpKnowledgeReadProjection,
            {"record": _http_record()},
            ({"kind": "list"}, {"operation": "store"}, {"created": False}),
        ),
        (
            LocalCommandHttpKnowledgeFindProjection,
            {"records": (), "truncated": False},
            (
                {"truncated": 0},
                {"kind": "list"},
                {"operation": "read"},
                {"x": 1},
            ),
        ),
    ),
)
def test_http_knowledge_projection_models_reject_invalid_contract(
    model, values, overrides
) -> None:
    for override in overrides:
        invalid = dict(values)
        invalid.update(override)
        with pytest.raises(ValidationError):
            model.model_validate(invalid)


def test_http_read_and_find_projection_exact_shapes_and_order() -> None:
    first = _http_record(record_id="second")
    second = _http_record(record_id="first", kind="state")
    read = LocalCommandHttpKnowledgeReadProjection(record=first)
    find = LocalCommandHttpKnowledgeFindProjection(
        records=(first, second), truncated=True
    )

    assert read.model_dump() == {
        "kind": "knowledge",
        "operation": "read",
        "record": first.model_dump(),
    }
    assert "created" not in read.model_dump()
    assert find.records == (first, second)
    assert LocalCommandHttpKnowledgeFindProjection(
        records=(), truncated=False
    ).records == ()


@pytest.mark.parametrize(
    ("projection", "expected_type"),
    (
        (
            {"kind": "list", "operation": "add", "list_id": "x", "added": [],
             "already_present": [], "items": []},
            LocalCommandHttpListAddProjection,
        ),
        (
            {"kind": "list", "operation": "read", "list_id": "x", "items": []},
            LocalCommandHttpListReadProjection,
        ),
        (
            {"kind": "knowledge", "operation": "store",
             "record": _http_record().model_dump(), "created": True},
            LocalCommandHttpKnowledgeStoreProjection,
        ),
        (
            {"kind": "knowledge", "operation": "read",
             "record": _http_record().model_dump()},
            LocalCommandHttpKnowledgeReadProjection,
        ),
        (
            {"kind": "knowledge", "operation": "find", "records": [],
             "truncated": False},
            LocalCommandHttpKnowledgeFindProjection,
        ),
    ),
)
def test_http_projection_union_resolves_outer_kind_then_operation(
    projection, expected_type
) -> None:
    response = LocalCommandHttpResponse(
        success=True, route="local", response="done", error=None,
        projection=projection,
    )
    assert type(response.projection) is expected_type


@pytest.mark.parametrize(
    "projection",
    (
        {"kind": "unknown", "operation": "read"},
        {"kind": "knowledge", "operation": "delete"},
    ),
)
def test_http_projection_union_rejects_unknown_kind_or_operation(projection) -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpResponse(
            success=True, route="local", response="done", error=None,
            projection=cast(Any, projection),
        )


@pytest.mark.parametrize(
    "route",
    (
        "local",
        "cognitive",
        "safe_insufficiency",
    ),
)
def test_http_response_accepts_only_public_routes(route) -> None:
    response = LocalCommandHttpResponse(
        success=True,
        route=route,
        response="result",
        error=None,
    )

    assert response.route == route


def test_http_response_rejects_unknown_route() -> None:
    with pytest.raises(ValidationError):
        LocalCommandHttpResponse(
            success=True,
            route=cast(Any, "internal_router"),
            response="result",
            error=None,
        )

_http_app = FastAPI()
_http_app.include_router(api_router)


class RecordingApplicationGateway:
    def __init__(
        self,
        result: object = None,
        *,
        exception: Exception | None = None,
    ) -> None:
        self.result = result
        self.exception = exception
        self.requests: list[object] = []

    def execute(self, request: object) -> object:
        self.requests.append(request)
        if self.exception is not None:
            raise self.exception
        return self.result


def _post_local_command_raw(
    body: bytes,
) -> tuple[int, dict[str, object] | str]:
    messages: list[dict[str, object]] = []
    request_sent = False

    async def receive() -> dict[str, object]:
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }

    async def send(message: dict[str, object]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/local/command",
        "raw_path": b"/local/command",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"content-type", b"application/json"),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    asyncio.run(
        _http_app(
            scope,
            receive,
            cast(Any, send),
        )
    )

    response_start = next(
        message
        for message in messages
        if message["type"] == "http.response.start"
    )

    response_body = b"".join(
        cast(bytes, message.get("body", b""))
        for message in messages
        if message["type"] == "http.response.body"
    )

    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        payload = response_body.decode()

    return (
        cast(int, response_start["status"]),
        cast(dict[str, object] | str, payload),
    )


def _post_local_command(
    payload: object,
) -> tuple[int, dict[str, object] | str]:
    return _post_local_command_raw(
        json.dumps(payload).encode()
    )


def _failure(
    code: LocalCommandApplicationErrorCode,
    route: LocalCommandApplicationRoute | None = None,
) -> LocalCommandApplicationResult:
    return LocalCommandApplicationResult(
        False,
        route=route,
        error=application_error(code),
    )


def test_local_command_route_is_registered_once() -> None:
    matches = [
        included
        for included in api_router.routes
        if getattr(included, "original_router", None)
        is local_command.router
    ]

    assert len(matches) == 1


def test_http_adapter_unwraps_proof_once_into_application_request(
    monkeypatch,
) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="completed locally",
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    proof = "proof-visible-only-to-application-boundary"

    status, payload = _post_local_command(
        _payload(
            proof=proof,
            allow_cognitive_fallback=True,
        )
    )

    assert status == 200
    assert payload == {
        "success": True,
        "route": "local",
        "response": "completed locally",
        "error": None,
    }

    assert len(gateway.requests) == 1

    application_request = gateway.requests[0]

    assert type(application_request) is LocalCommandApplicationRequest
    assert application_request.proof == proof
    assert application_request.requested_workspace_id == "workspace"
    assert application_request.text == "list read groceries"
    assert application_request.allow_cognitive_fallback is True
    assert proof not in repr(application_request)


@pytest.mark.parametrize(
    ("route", "response"),
    (
        (
            LocalCommandApplicationRoute.LOCAL,
            "local result",
        ),
        (
            LocalCommandApplicationRoute.COGNITIVE,
            "cognitive result",
        ),
    ),
)
def test_http_adapter_maps_success_to_200(
    monkeypatch,
    route,
    response,
) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=route,
            response=response,
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    assert payload == {
        "success": True,
        "route": route.value,
        "response": response,
        "error": None,
    }
    assert "projection" not in payload


@pytest.mark.parametrize(
    ("added", "already_present", "items"),
    (
        (("milk", "eggs"), (), ("milk", "eggs")),
        ((), ("milk", "eggs"), ("eggs", "milk")),
    ),
)
def test_http_adapter_maps_add_projection_to_exact_wire_contract(
    monkeypatch,
    added,
    already_present,
    items,
) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="List updated locally.",
            projection=LocalListAddProjection(
                list_id="groceries",
                added=added,
                already_present=already_present,
                items=items,
            ),
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    assert payload == {
        "success": True,
        "route": "local",
        "response": "List updated locally.",
        "error": None,
        "projection": {
            "kind": "list",
            "operation": "add",
            "list_id": "groceries",
            "added": list(added),
            "already_present": list(already_present),
            "items": list(items),
        },
    }


@pytest.mark.parametrize("items", (("milk", "eggs"), ()))
def test_http_adapter_maps_read_projection_to_exact_wire_contract(
    monkeypatch,
    items,
) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="List read locally.",
            projection=LocalListReadProjection("groceries", items),
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    assert payload == {
        "success": True,
        "route": "local",
        "response": "List read locally.",
        "error": None,
        "projection": {
            "kind": "list",
            "operation": "read",
            "list_id": "groceries",
            "items": list(items),
        },
    }


def _application_record(
    record_id: str = "record",
    *,
    kind: LocalKnowledgeRecordKind = LocalKnowledgeRecordKind.FACT,
    key: str = "key",
    value: str = "value",
) -> LocalKnowledgeRecordProjection:
    return LocalKnowledgeRecordProjection(record_id, kind, key, value)


@pytest.mark.parametrize("created", (True, False))
def test_http_adapter_maps_store_projection_to_exact_json(
    monkeypatch, created
) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="Knowledge record stored locally.",
            projection=LocalKnowledgeStoreProjection(
                _application_record(), created
            ),
        )
    )
    monkeypatch.setattr(
        local_command.container, "local_command_application_gateway", gateway
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    assert payload == {
        "success": True,
        "route": "local",
        "response": "Knowledge record stored locally.",
        "error": None,
        "projection": {
            "kind": "knowledge",
            "operation": "store",
            "record": {
                "record_id": "record",
                "kind": "fact",
                "key": "key",
                "value": "value",
            },
            "created": created,
        },
    }


def test_http_adapter_maps_read_projection_without_created(monkeypatch) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="Knowledge record read locally.",
            projection=LocalKnowledgeReadProjection(
                _application_record(kind=LocalKnowledgeRecordKind.CONCEPT)
            ),
        )
    )
    monkeypatch.setattr(
        local_command.container, "local_command_application_gateway", gateway
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    projection = _require_http_payload(payload)["projection"]
    assert projection == {
        "kind": "knowledge",
        "operation": "read",
        "record": {
            "record_id": "record",
            "kind": "concept",
            "key": "key",
            "value": "value",
        },
    }
    assert "created" not in projection


@pytest.mark.parametrize(
    ("records", "truncated"),
    (((), False), ((_application_record("record-1"),), False),
     (tuple(_application_record(f"record-{index}") for index in range(50)), True)),
)
def test_http_adapter_maps_find_projection_preserving_order(
    monkeypatch, records, truncated
) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="Knowledge records found locally.",
            projection=LocalKnowledgeFindProjection(records, truncated),
        )
    )
    monkeypatch.setattr(
        local_command.container, "local_command_application_gateway", gateway
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    projection = _require_http_payload(payload)["projection"]
    assert projection["kind"] == "knowledge"
    assert projection["operation"] == "find"
    assert projection["truncated"] is truncated
    assert [item["record_id"] for item in projection["records"]] == [
        record.record_id for record in records
    ]


def test_http_adapter_preserves_hostile_record_strings_as_data(monkeypatch) -> None:
    hostile = (
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "https://example.invalid/path",
        "C:\\private\\path & <quoted>",
    )
    records = tuple(
        _application_record(
            f"record-{index}", key=hostile[index], value=value
        )
        for index, value in enumerate(reversed(hostile))
    )
    result = LocalCommandApplicationResult(
        True,
        route=LocalCommandApplicationRoute.LOCAL,
        response="Knowledge records found locally.",
        projection=LocalKnowledgeFindProjection(records, False),
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        RecordingApplicationGateway(result),
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    projected = _require_http_payload(payload)["projection"]["records"]
    assert [item["key"] for item in projected] == list(hostile)
    assert [item["value"] for item in projected] == list(reversed(hostile))
    serialized = json.dumps(payload)
    assert "workspace" not in serialized
    assert "source_type" not in serialized
    assert "source_reference" not in serialized
    assert "provenance" not in serialized


def test_unknown_application_projection_mapping_is_sanitized(monkeypatch) -> None:
    result = LocalCommandApplicationResult(
        True,
        route=LocalCommandApplicationRoute.LOCAL,
        response="completed",
    )
    object.__setattr__(result, "projection", object())
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        RecordingApplicationGateway(result),
    )

    status, payload = _post_local_command(_payload())

    assert status == 500
    assert payload == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "internal_error",
            "message": "The request could not be completed.",
        },
    }


def test_http_adapter_omits_only_absent_projection(monkeypatch) -> None:
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="completed locally",
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == 200
    assert payload == {
        "success": True,
        "route": "local",
        "response": "completed locally",
        "error": None,
    }
    assert "projection" not in payload


@pytest.mark.parametrize(
    ("code", "route", "expected_status"),
    (
        (
            LocalCommandApplicationErrorCode.INVALID_REQUEST,
            None,
            400,
        ),
        (
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
            None,
            403,
        ),
        (
            LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED,
            LocalCommandApplicationRoute.LOCAL,
            403,
        ),
        (
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND,
            LocalCommandApplicationRoute.LOCAL,
            404,
        ),
        (
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT,
            LocalCommandApplicationRoute.LOCAL,
            409,
        ),
        (
            LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED,
            LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            409,
        ),
        (
            LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED,
            LocalCommandApplicationRoute.LOCAL,
            503,
        ),
        (
            LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED,
            LocalCommandApplicationRoute.COGNITIVE,
            503,
        ),
        (
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
            None,
            503,
        ),
        (
            LocalCommandApplicationErrorCode.INTERNAL_ERROR,
            None,
            500,
        ),
    ),
)
def test_http_adapter_has_closed_failure_status_mapping(
    monkeypatch,
    code,
    route,
    expected_status,
) -> None:
    result = _failure(code, route)
    gateway = RecordingApplicationGateway(result)

    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == expected_status
    assert payload == {
        "success": False,
        "route": route.value if route is not None else None,
        "response": None,
        "error": {
            "code": code.value,
            "message": _application_error_message(result),
        },
    }
    assert "projection" not in payload


def test_http_adapter_maps_safe_insufficiency_invalid_input_to_400(
    monkeypatch,
) -> None:
    result = _failure(
        LocalCommandApplicationErrorCode.INVALID_REQUEST,
        LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
    )
    gateway = RecordingApplicationGateway(result)

    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == 400
    assert _require_http_payload(payload)["route"] == "safe_insufficiency"
    assert _http_error_code(payload) == "invalid_request"


def test_default_http_path_fails_closed() -> None:
    status, payload = _post_local_command(_payload())

    assert status == 403
    assert payload == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "access_denied",
            "message": "Access denied.",
        },
    }


@pytest.mark.parametrize(
    "invalid_payload",
    (
        {
            "proof": "safe-proof",
            "requested_workspace_id": "workspace",
            "text": "list read groceries",
            "allow_cognitive_fallback": "false",
        },
        {
            "proof": "safe-proof",
            "requested_workspace_id": "workspace",
            "text": "list read groceries",
        },
        {
            "proof": "safe-proof",
            "requested_workspace_id": "   ",
            "text": "list read groceries",
            "allow_cognitive_fallback": False,
        },
        {
            "proof": "   ",
            "requested_workspace_id": "workspace",
            "text": "list read groceries",
            "allow_cognitive_fallback": False,
        },
        {
            "proof": "safe-proof",
            "requested_workspace_id": "workspace",
            "text": "list read groceries",
            "allow_cognitive_fallback": False,
            "unexpected": "forbidden",
        },
    ),
)
def test_http_validation_is_400_not_fastapi_422_and_never_calls_gateway(
    monkeypatch,
    invalid_payload,
) -> None:
    gateway = RecordingApplicationGateway(
        exception=AssertionError(
            "Gateway must not run for invalid transport input."
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(invalid_payload)

    assert status == 400
    assert payload == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "invalid_request",
            "message": "The request is invalid.",
        },
    }
    assert "projection" not in payload
    assert gateway.requests == []


def test_http_validation_failure_does_not_expose_valid_proof(
    monkeypatch,
) -> None:
    proof = "proof-that-must-never-reach-response"

    gateway = RecordingApplicationGateway(
        exception=AssertionError(
            "Gateway must not run."
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(
        _payload(
            proof=proof,
            allow_cognitive_fallback="invalid",
        )
    )

    serialized = json.dumps(payload)

    assert status == 400
    assert proof not in serialized
    assert gateway.requests == []


def test_malformed_json_is_fixed_400_without_gateway_invocation(
    monkeypatch,
) -> None:
    gateway = RecordingApplicationGateway(
        exception=AssertionError(
            "Gateway must not run for malformed JSON."
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    proof = "proof-inside-malformed-json"

    body = (
        b'{"proof":"'
        + proof.encode()
        + b'","requested_workspace_id":"workspace"'
    )

    status, payload = _post_local_command_raw(body)

    serialized = json.dumps(payload)

    assert status == 400
    assert _http_error_code(payload) == "invalid_request"
    assert proof not in serialized
    assert gateway.requests == []


def test_non_object_json_is_fixed_400_without_gateway_invocation(
    monkeypatch,
) -> None:
    gateway = RecordingApplicationGateway(
        exception=AssertionError(
            "Gateway must not run for non-object JSON."
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(["not", "an", "object"])

    assert status == 400
    assert _http_error_code(payload) == "invalid_request"
    assert gateway.requests == []


def test_unexpected_gateway_exception_is_fixed_sanitized_500(
    monkeypatch,
) -> None:
    proof = "proof-that-must-not-leak"
    internal_detail = (
        "provider http://private-host "
        "C:\\secret\\model "
        + proof
    )

    gateway = RecordingApplicationGateway(
        exception=RuntimeError(internal_detail)
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(
        _payload(proof=proof)
    )

    assert status == 500
    assert payload == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "internal_error",
            "message": "The request could not be completed.",
        },
    }
    assert "projection" not in payload

    serialized = json.dumps(payload)

    assert proof not in serialized
    assert internal_detail not in serialized
    assert "http://private-host" not in serialized
    assert "C:\\secret" not in serialized


def test_invalid_gateway_result_is_fixed_sanitized_500(
    monkeypatch,
) -> None:
    gateway = RecordingApplicationGateway(
        object()
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    status, payload = _post_local_command(_payload())

    assert status == 500
    assert payload == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "internal_error",
            "message": "The request could not be completed.",
        },
    }
    assert "projection" not in payload


def test_projection_mapping_failure_is_fixed_sanitized_500(
    monkeypatch,
) -> None:
    detail = "projection detail that must not leak"
    gateway = RecordingApplicationGateway(
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="List read locally.",
            projection=LocalListReadProjection("groceries", ("milk",)),
        )
    )
    monkeypatch.setattr(
        local_command.container,
        "local_command_application_gateway",
        gateway,
    )

    def fail_mapping(projection):
        raise RuntimeError(detail)

    monkeypatch.setattr(local_command, "_map_projection", fail_mapping)

    status, payload = _post_local_command(_payload())

    assert status == 500
    assert payload == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "internal_error",
            "message": "The request could not be completed.",
        },
    }
    assert "projection" not in payload
    assert detail not in json.dumps(payload)

def test_http_workspace_limit_applies_after_trimming() -> None:
    workspace_id = " " + ("w" * WORKSPACE_ID_MAX_LENGTH) + " "

    request = LocalCommandHttpRequest.model_validate(
        _payload(requested_workspace_id=workspace_id)
    )

    assert request.requested_workspace_id == (
        "w" * WORKSPACE_ID_MAX_LENGTH
    )


def test_http_workspace_rejects_oversized_normalized_value() -> None:
    workspace_id = (
        " "
        + ("w" * (WORKSPACE_ID_MAX_LENGTH + 1))
        + " "
    )

    with pytest.raises(ValidationError):
        LocalCommandHttpRequest.model_validate(
            _payload(requested_workspace_id=workspace_id)
        )


@pytest.mark.parametrize("kind", ("fact", "concept", "state"))
@pytest.mark.parametrize("continuation", (False, True))
def test_http_browse_summary_closed_frozen_and_literal(kind, continuation):
    from app.api.models.local_command import (
        LocalCommandHttpKnowledgeBrowseProjection,
        LocalCommandHttpKnowledgeSummary,
    )

    if continuation:
        from app.api.models.local_command import (
            LocalCommandHttpKnowledgeBrowseAfterProjection,
        )
        LocalCommandHttpKnowledgeBrowseProjection = (
            LocalCommandHttpKnowledgeBrowseAfterProjection
        )

    summary = LocalCommandHttpKnowledgeSummary(
        record_id='id"\\e\u0301', kind=kind, key="key  e\u0301"
    )
    assert summary.model_dump() == {
        "record_id": 'id"\\e\u0301',
        "kind": kind,
        "key": "key  e\u0301",
    }
    with pytest.raises(ValidationError):
        summary.key = "changed"
    projection = LocalCommandHttpKnowledgeBrowseProjection(
        records=(summary,), truncated=False
    )
    assert set(projection.model_dump()) == {"kind", "operation", "records", "truncated"}
    with pytest.raises(ValidationError):
        projection.truncated = True
    envelope = LocalCommandHttpResponse(
        success=True,
        route="local",
        response="Done",
        error=None,
        projection=projection.model_dump(),
    )
    assert type(envelope.projection) is LocalCommandHttpKnowledgeBrowseProjection


@pytest.mark.parametrize(
    "field,value",
    (
        ("record_id", 1),
        ("key", True),
        ("kind", "unknown"),
        ("value", "private"),
        ("provenance", {}),
        ("workspace", "w"),
        ("total", 1),
        ("cursor", "x"),
        ("key", " key"),
    ),
)
def test_http_browse_summary_rejects_types_and_extras(field, value):
    from app.api.models.local_command import LocalCommandHttpKnowledgeSummary

    args = dict(record_id="id", kind="fact", key="key")
    args[field] = value
    with pytest.raises(ValidationError):
        LocalCommandHttpKnowledgeSummary(**args)


@pytest.mark.parametrize(
    "override",
    (
        {"truncated": 0},
        {"truncated": "false"},
        {"truncated": True},
        {"value": "private"},
        {"workspace": "w"},
        {"total": 0},
        {"cursor": None},
        {"operation": "find"},
        {"kind": "list"},
    ),
)
@pytest.mark.parametrize("continuation", (False, True))
def test_http_browse_projection_rejects_invalid_contract(override, continuation):
    from app.api.models.local_command import LocalCommandHttpKnowledgeBrowseProjection

    if continuation:
        from app.api.models.local_command import (
            LocalCommandHttpKnowledgeBrowseAfterProjection,
        )
        LocalCommandHttpKnowledgeBrowseProjection = (
            LocalCommandHttpKnowledgeBrowseAfterProjection
        )

    args = dict(records=(), truncated=False)
    args.update(override)
    with pytest.raises(ValidationError):
        LocalCommandHttpKnowledgeBrowseProjection(**args)


@pytest.fixture
def browse_http_runtime(tmp_path, monkeypatch, request):
    from app.core.container import Container
    from app.infrastructure.local_storage.sqlite_storage import SQLiteLocalStorage
    from app.operations import local_interactive_runtime as runtime_module
    from app.operations.local_interactive_runtime import (
        DEVELOPMENT_WORKSPACE,
        LocalInteractiveRuntime,
    )

    captured = []

    def compose(*args, **kwargs):
        parameters = getattr(getattr(request.node, "callspec", None), "params", {})
        if parameters.get("scenario") == "missing":
            kwargs.pop(
                "local_knowledge_browse_after_repository"
                if parameters.get("continuation")
                else "local_knowledge_browse_repository"
            )
        instance = Container(*args, **kwargs)
        captured.append(instance)
        return instance

    monkeypatch.setattr(runtime_module, "Container", compose)
    path = tmp_path / "browse-http.sqlite3"
    runtime = LocalInteractiveRuntime(path, "temporary-browse-proof")
    runtime.start()
    storage = SQLiteLocalStorage(path)
    storage.open()
    storage.initialize()
    monkeypatch.setattr(
        _http_app.state,
        "local_command_application_gateway",
        runtime.gateway,
        raising=False,
    )

    def post(text, fallback=False):
        return _post_local_command(
            _payload(
                proof="temporary-browse-proof",
                requested_workspace_id=DEVELOPMENT_WORKSPACE.workspace_id,
                text=text,
                allow_cognitive_fallback=fallback,
            )
        )

    try:
        yield captured[0], storage, post
    finally:
        storage.close()
        runtime.close()


@pytest.mark.parametrize("fallback", (False, True))
@pytest.mark.parametrize(
    "scenario",
    (
        "empty",
        "success",
        "full",
        "truncated",
        "invalid",
        "denied",
        "declared",
        "unexpected",
        "missing",
        "gateway_corrupt",
    ),
)
@pytest.mark.parametrize("continuation", (False, True))
def test_browse_http_integrated_terminals(
    browse_http_runtime, fallback, scenario, continuation
):
    from unittest.mock import patch

    from app.cognition.local_resolution.contracts import LocalRepositoryError
    from app.cognition.local_resolution.models import (
        KnowledgeKind,
        KnowledgeProvenance,
        KnowledgeRecord,
    )
    from app.cognition.local_resolution.permissions import KNOWLEDGE_RECORDS_BROWSE
    from app.infrastructure.local_storage.sqlite_storage import (
        SQLitePermissionGrantRepository,
    )
    from app.operations.local_interactive_runtime import (
        DEVELOPMENT_ACTOR,
        DEVELOPMENT_WORKSPACE,
    )

    instance, storage, post = browse_http_runtime
    anchor = "PRIVATE_ANCHOR"
    operation = "browse-after" if continuation else "browse"
    method = "browse_after" if continuation else "browse"
    total = {"success": 1, "full": 50, "truncated": 51}.get(scenario, 0)
    for i in reversed(range(total)):
        instance.local_knowledge_repository.store(
            KnowledgeRecord(
                f"id-{i:03}",
                DEVELOPMENT_WORKSPACE,
                (KnowledgeKind.FACT, KnowledgeKind.CONCEPT, KnowledgeKind.STATE)[i % 3],
                "key  e\u0301",
                "PRIVATE_VALUE",
                KnowledgeProvenance("explicit", "PRIVATE_SOURCE"),
            )
        )
    if scenario == "denied":
        SQLitePermissionGrantRepository(storage).revoke(
            DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE, KNOWLEDGE_RECORDS_BROWSE
        )
    repository = instance.local_knowledge_repository
    with (
        patch.object(repository, method, wraps=getattr(repository, method)) as browse,
        patch.object(
            instance.local_command_interpreter,
            "interpret",
            wraps=instance.local_command_interpreter.interpret,
        ) as interpreter,
        patch.object(
            instance.cognitive_engine,
            "process",
            wraps=instance.cognitive_engine.process,
        ) as cognitive,
        patch.object(instance.ollama_client, "chat") as model,
        patch.object(instance.provider_readiness_probe, "check") as readiness,
        patch("requests.get") as network_get,
        patch("requests.post") as network_post,
        patch.object(
            instance.local_first_resolver,
            "resolve",
            wraps=instance.local_first_resolver.resolve,
        ) as resolve,
    ):
        if scenario == "declared":
            browse.side_effect = LocalRepositoryError("PRIVATE_STORAGE")
        if scenario == "unexpected":
            browse.side_effect = RuntimeError("PRIVATE_STORAGE")
        if scenario == "gateway_corrupt":
            original = instance.local_first_resolver.__class__.resolve

            def corrupt(*args):
                result = original(instance.local_first_resolver, *args)
                from app.cognition.local_resolution.models import (
                    KnowledgeBrowseResolutionResult,
                )

                if type(result) is KnowledgeBrowseResolutionResult:
                    object.__setattr__(result, "truncated", True)
                return result

            resolve.side_effect = corrupt
        status, body = post(
            f"knowledge {operation} :: []"
            if scenario == "invalid"
            else f"knowledge {operation} :: "
            + json.dumps({"after_record_id": anchor} if continuation else {}),
            fallback,
        )
        expected = {
            "invalid": 400,
            "denied": 403,
            "declared": 503,
            "unexpected": 500,
            "missing": 503,
            "gateway_corrupt": 500,
        }.get(scenario, 200)
        assert status == expected
        assert browse.call_count == (scenario not in ("invalid", "denied", "missing"))
        if browse.called:
            browse.assert_called_once_with(
                DEVELOPMENT_WORKSPACE, *((anchor,) if continuation else ())
            )
        interpreter.assert_called_once()
        cognitive.assert_not_called()
        if expected == 200:
            assert body == {
                "success": True,
                "route": "local",
                "response": "Knowledge records browsed locally.",
                "error": None,
                "projection": {
                    "kind": "knowledge",
                    "operation": "browse_after" if continuation else "browse",
                    "records": [
                        {
                            "record_id": f"id-{i:03}",
                            "kind": ("fact", "concept", "state")[i % 3],
                            "key": "key  e\u0301",
                        }
                        for i in range(min(total, 50))
                    ],
                    "truncated": total == 51,
                },
            }
        else:
            codes = {
                400: "invalid_request",
                403: "local_permission_denied",
                503: "local_validation_failed",
                500: "internal_error",
            }
            assert body["error"]["code"] == codes[expected]
            assert body["response"] is None and "projection" not in body
            if expected == 500:
                assert body == local_command._INTERNAL_ERROR_CONTENT
        serialized = json.dumps(body)
        for private in (
            "PRIVATE_",
            DEVELOPMENT_ACTOR.actor_id,
            DEVELOPMENT_WORKSPACE.workspace_id,
            "after_record_id",
            "source_type",
            "source_reference",
            "provenance",
            "id-050",
        ):
            assert private not in serialized
        # Same real pipeline and observed engine: unrelated authorized text invokes it.
        _, positive = post("ordinary cognitive input", True)
        assert positive["route"] == "cognitive"
        cognitive.assert_called_once_with("ordinary cognitive input")
        model.assert_not_called()
        readiness.assert_not_called()
        network_get.assert_not_called()
        network_post.assert_not_called()


@pytest.mark.parametrize("fallback", (False, True))
def test_http_browse_then_read_reauthorizes_without_runtime_restart(
    browse_http_runtime, fallback
):
    from unittest.mock import patch

    from app.cognition.local_resolution.permissions import KNOWLEDGE_RECORDS_READ
    from app.infrastructure.local_storage.sqlite_storage import (
        SQLitePermissionGrantRepository,
    )
    from app.operations.local_interactive_runtime import (
        DEVELOPMENT_ACTOR,
        DEVELOPMENT_WORKSPACE,
    )

    instance, storage, post = browse_http_runtime
    status, _ = post(
        'knowledge store :: {"record_id":"id","kind":"fact","key":"key",'
        '"value":"private value","source_type":"explicit",'
        '"source_reference":"private source"}',
        fallback,
    )
    assert status == 200
    assert post("knowledge browse :: {}", fallback)[0] == 200
    status, read = post('knowledge read :: {"record_id":"id"}', fallback)
    assert status == 200 and read["projection"]["record"]["value"] == "private value"
    assert post('knowledge read :: {"record_id":"missing"}', fallback)[0] == 404
    SQLitePermissionGrantRepository(storage).revoke(
        DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE, KNOWLEDGE_RECORDS_READ
    )
    assert post("knowledge browse :: {}", fallback)[0] == 200
    with patch.object(
        instance.local_knowledge_repository,
        "read",
        wraps=instance.local_knowledge_repository.read,
    ) as read_port:
        status, denied = post('knowledge read :: {"record_id":"id"}', fallback)
        assert status == 403 and denied["error"]["code"] == "local_permission_denied"
        assert "projection" not in denied
        read_port.assert_not_called()


@pytest.mark.parametrize("corruption", ("duplicate", "order", "excess"))
@pytest.mark.parametrize("continuation", (False, True))
def test_http_browse_model_rejects_corrupt_sequences(corruption, continuation):
    from app.api.models.local_command import LocalCommandHttpKnowledgeBrowseProjection

    if continuation:
        from app.api.models.local_command import (
            LocalCommandHttpKnowledgeBrowseAfterProjection,
        )
        LocalCommandHttpKnowledgeBrowseProjection = (
            LocalCommandHttpKnowledgeBrowseAfterProjection
        )

    records = [
        dict(record_id=f"id-{i:03}", kind="fact", key="key")
        for i in range(51 if corruption == "excess" else 2)
    ]
    if corruption == "duplicate":
        records[1] = records[0]
    if corruption == "order":
        records.reverse()
    with pytest.raises(ValidationError):
        LocalCommandHttpKnowledgeBrowseProjection(records=records, truncated=False)


@pytest.mark.parametrize(
    "field,value",
    (
        ("truncated", 0),
        ("kind", "list"),
        ("operation", "find"),
        ("records", (object(),)),
    ),
)
@pytest.mark.parametrize("continuation", (False, True))
def test_http_browse_corrupt_application_projection_is_sanitized(
    monkeypatch, field, value, continuation
):
    from app.local_command import LocalKnowledgeBrowseProjection

    if continuation:
        from app.local_command import (
            LocalKnowledgeBrowseAfterProjection as LocalKnowledgeBrowseProjection,
        )
    projection = LocalKnowledgeBrowseProjection((), False)
    result = LocalCommandApplicationResult(
        True, LocalCommandApplicationRoute.LOCAL, "Done", projection=projection
    )
    object.__setattr__(projection, field, value)
    gateway = RecordingApplicationGateway(result)
    monkeypatch.setattr(local_command, "_resolve_gateway", lambda request: gateway)
    status, body = _post_local_command(_payload(text="knowledge browse :: {}"))
    assert status == 500 and body == local_command._INTERNAL_ERROR_CONTENT


@pytest.mark.parametrize("fallback", (False, True))
def test_http_browse_after_revocation_without_restart(browse_http_runtime, fallback):
    from unittest.mock import patch

    from app.cognition.local_resolution.permissions import KNOWLEDGE_RECORDS_BROWSE
    from app.infrastructure.local_storage.sqlite_storage import (
        SQLitePermissionGrantRepository,
    )
    from app.operations.local_interactive_runtime import (
        DEVELOPMENT_ACTOR,
        DEVELOPMENT_WORKSPACE,
    )

    instance, storage, post = browse_http_runtime
    assert (
        post(
            'knowledge store :: {"record_id":"record","kind":"fact","key":"key",'
            '"value":"PRIVATE_VALUE","source_type":"explicit",'
            '"source_reference":"PRIVATE_SOURCE"}',
            fallback,
        )[0]
        == 200
    )
    command = 'knowledge browse-after :: {"after_record_id":"PRIVATE_ANCHOR"}'
    status, body = post(command, fallback)
    assert status == 200 and body["projection"]["operation"] == "browse_after"
    assert [r["record_id"] for r in body["projection"]["records"]] == ["record"]
    SQLitePermissionGrantRepository(storage).revoke(
        DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE, KNOWLEDGE_RECORDS_BROWSE
    )
    with patch.object(instance.local_knowledge_repository, "browse_after") as data:
        status, body = post(command, fallback)
        assert status == 403 and body["error"]["code"] == "local_permission_denied"
        assert "projection" not in body and body["response"] is None
        assert "PRIVATE_" not in json.dumps(body)
        data.assert_not_called()


@pytest.mark.parametrize(
    "field",
    (
        "after_record_id",
        "anchor",
        "actor",
        "workspace_id",
        "value",
        "provenance",
        "total",
        "cursor",
        "page",
    ),
)
def test_http_browse_after_projection_rejects_private_fields(field):
    from app.api.models.local_command import (
        LocalCommandHttpKnowledgeBrowseAfterProjection,
    )

    with pytest.raises(ValidationError):
        LocalCommandHttpKnowledgeBrowseAfterProjection(
            records=(), truncated=False, **{field: "PRIVATE_SENTINEL"}
        )
