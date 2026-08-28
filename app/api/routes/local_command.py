"""Local-only HTTP adapter for authenticated local commands."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.models.local_command import (
    LocalCommandHttpError,
    LocalCommandHttpListAddProjection,
    LocalCommandHttpListProjection,
    LocalCommandHttpListReadProjection,
    LocalCommandHttpRequest,
    LocalCommandHttpResponse,
)
from app.core.container import container
from app.local_command import (
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationGateway,
    LocalCommandApplicationRequest,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    LocalListAddProjection,
    LocalListReadProjection,
    application_error,
)

router = APIRouter(
    prefix="/local",
    tags=["Local Command"],
)


_HTTP_STATUS_BY_ERROR_CODE = {
    LocalCommandApplicationErrorCode.INVALID_REQUEST: 400,
    LocalCommandApplicationErrorCode.ACCESS_DENIED: 403,
    LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED: 403,
    LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND: 404,
    LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT: 409,
    LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED: 409,
    LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED: 503,
    LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED: 503,
    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE: 503,
    LocalCommandApplicationErrorCode.INTERNAL_ERROR: 500,
}

_INTERNAL_ERROR_CONTENT = {
    "success": False,
    "route": None,
    "response": None,
    "error": {
        "code": "internal_error",
        "message": "The request could not be completed.",
    },
}

_MISSING_GATEWAY = object()


def _fixed_internal_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_INTERNAL_ERROR_CONTENT,
    )


def _resolve_gateway(request: Request) -> LocalCommandApplicationGateway:
    gateway = getattr(
        request.app.state,
        "local_command_application_gateway",
        _MISSING_GATEWAY,
    )
    if gateway is _MISSING_GATEWAY:
        return container.local_command_application_gateway
    if not isinstance(gateway, LocalCommandApplicationGateway):
        raise TypeError("The injected application gateway is invalid.")
    return gateway


def _failure_result(
    code: LocalCommandApplicationErrorCode,
    route: LocalCommandApplicationRoute | None = None,
) -> LocalCommandApplicationResult:
    return LocalCommandApplicationResult(
        False,
        route=route,
        error=application_error(code),
    )


def _map_projection(
    projection: object | None,
) -> LocalCommandHttpListProjection | None:
    if projection is None:
        return None
    if type(projection) is LocalListAddProjection:
        return LocalCommandHttpListAddProjection(
            list_id=projection.list_id,
            added=projection.added,
            already_present=projection.already_present,
            items=projection.items,
        )
    if type(projection) is LocalListReadProjection:
        return LocalCommandHttpListReadProjection(
            list_id=projection.list_id,
            items=projection.items,
        )
    raise TypeError("Application projection type is invalid.")


def _wire_payload(payload: LocalCommandHttpResponse) -> dict[str, object]:
    content = payload.model_dump(mode="json")
    if payload.projection is None:
        content.pop("projection")
    return content


def _render_result(
    result: LocalCommandApplicationResult,
) -> JSONResponse:
    if type(result) is not LocalCommandApplicationResult:
        raise TypeError(
            "Application gateway returned an invalid result."
        )

    if result.success:
        payload = LocalCommandHttpResponse(
            success=True,
            route=result.route.value if result.route is not None else None,
            response=result.response,
            error=None,
            projection=_map_projection(result.projection),
        )
        return JSONResponse(
            status_code=200,
            content=_wire_payload(payload),
        )

    application_error = result.error
    if application_error is None:
        raise TypeError(
            "Failure application result must include an error."
        )

    error = LocalCommandHttpError(
        code=application_error.code.value,
        message=application_error.message,
    )

    payload = LocalCommandHttpResponse(
        success=False,
        route=result.route.value if result.route is not None else None,
        response=None,
        error=error,
    )

    return JSONResponse(
        status_code=_HTTP_STATUS_BY_ERROR_CODE[
            application_error.code
        ],
        content=_wire_payload(payload),
    )


@router.post("/command")
async def execute_local_command(request: Request) -> JSONResponse:
    """Validate one JSON request and delegate once to the application gateway."""

    try:
        body = await request.body()
        raw_payload = json.loads(body)

        transport_request = LocalCommandHttpRequest.model_validate(
            raw_payload
        )

        application_request = LocalCommandApplicationRequest(
            proof=transport_request.proof.get_secret_value(),
            requested_workspace_id=(
                transport_request.requested_workspace_id
            ),
            text=transport_request.text,
            allow_cognitive_fallback=(
                transport_request.allow_cognitive_fallback
            ),
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValidationError,
        ValueError,
    ):
        return _render_result(
            _failure_result(
                LocalCommandApplicationErrorCode.INVALID_REQUEST
            )
        )
    except Exception:
        return _fixed_internal_error_response()

    try:
        gateway = _resolve_gateway(request)
        result = gateway.execute(application_request)
        return _render_result(result)
    except Exception:
        return _fixed_internal_error_response()
