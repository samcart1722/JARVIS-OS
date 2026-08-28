"""Transport-boundary tests for authenticated local commands."""
import asyncio
import json
from typing import Any, cast

import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from app.api.models.local_command import (
    LocalCommandHttpError,
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
