"""Separate FastAPI composition for the local interactive runtime."""

from contextlib import asynccontextmanager
from hmac import compare_digest

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.routes.local_command import router as local_command_router
from app.api.routes.local_ui import create_local_ui_router
from app.operations.local_interactive_runtime import LocalInteractiveRuntime

_GATEWAY_STATE_KEY = "local_command_application_gateway"
HOST_HEADER_VALUE = "127.0.0.1:8765"
ORIGIN_VALUE = "http://127.0.0.1:8765"

_TRANSPORT_REJECTION_CONTENT = {
    "success": False,
    "route": None,
    "response": None,
    "error": {
        "code": "local_transport_rejected",
        "message": "The local request was rejected.",
    },
}


def _single_header(scope: Scope, name: bytes) -> str | None:
    values = [
        value.decode("latin-1")
        for header_name, value in scope.get("headers", ())
        if header_name.lower() == name
    ]
    if len(values) != 1:
        return None
    return values[0]


def _is_accepted_json_content_type(value: str | None) -> bool:
    if value is None:
        return False
    parts = value.split(";")
    if parts[0].strip().lower() != "application/json":
        return False
    if len(parts) == 1:
        return True
    if len(parts) != 2:
        return False
    parameter = parts[1].split("=")
    return (
        len(parameter) == 2
        and parameter[0].strip().lower() == "charset"
        and parameter[1].strip().lower() == "utf-8"
    )


class _StrictInteractiveTransportPolicy:
    def __init__(
        self,
        app: ASGIApp,
        runtime: LocalInteractiveRuntime,
    ) -> None:
        self._app = app
        self._runtime = runtime

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        if _single_header(scope, b"host") != HOST_HEADER_VALUE:
            await self._reject(scope, receive, send, 400)
            return

        if scope["method"] == "POST" and scope["path"] == "/local/command":
            if _single_header(scope, b"origin") != ORIGIN_VALUE:
                await self._reject(scope, receive, send, 403)
                return
            if not _is_accepted_json_content_type(
                _single_header(scope, b"content-type")
            ):
                await self._reject(scope, receive, send, 415)
                return
            supplied_csrf = _single_header(scope, b"x-luxiom-csrf")
            try:
                expected_csrf = self._runtime.csrf_token
                csrf_matches = (
                    supplied_csrf is not None
                    and compare_digest(supplied_csrf, expected_csrf)
                )
            except Exception:
                csrf_matches = False
            if not csrf_matches:
                await self._reject(scope, receive, send, 403)
                return

        await self._app(scope, receive, send)

    @staticmethod
    async def _reject(
        scope: Scope,
        receive: Receive,
        send: Send,
        status_code: int,
    ) -> None:
        response = JSONResponse(
            status_code=status_code,
            content=_TRANSPORT_REJECTION_CONTENT,
        )
        await response(scope, receive, send)


def create_local_interactive_app(
    runtime: LocalInteractiveRuntime,
) -> FastAPI:
    """Create an inert interactive app whose lifespan owns one runtime."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            runtime.start()
            setattr(app.state, _GATEWAY_STATE_KEY, runtime.gateway)
            yield
        finally:
            if hasattr(app.state, _GATEWAY_STATE_KEY):
                delattr(app.state, _GATEWAY_STATE_KEY)
            runtime.close()

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(_StrictInteractiveTransportPolicy, runtime=runtime)
    app.include_router(local_command_router)
    app.include_router(create_local_ui_router(lambda: runtime.csrf_token))
    return app
