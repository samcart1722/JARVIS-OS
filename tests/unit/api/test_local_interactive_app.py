import asyncio
import json
from dataclasses import fields
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI

from app.api.models.local_command import LocalCommandHttpResponse
from app.api.routes import local_command
from app.local_command import (
    LocalCommandApplicationGateway,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
)
from app.operations.local_interactive_runtime import (
    DEVELOPMENT_WORKSPACE,
    LocalInteractiveRuntime,
    LocalInteractiveRuntimeError,
    LocalInteractiveRuntimeState,
)

TEST_PROOF = "sprint34-b2-test-proof"
_STATE_GATEWAY = "local_command_application_gateway"
INTERACTIVE_HOST = "127.0.0.1:8765"
INTERACTIVE_ORIGIN = "http://127.0.0.1:8765"


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "proof": TEST_PROOF,
        "requested_workspace_id": DEVELOPMENT_WORKSPACE.workspace_id,
        "text": "list read sprint34-b2",
        "allow_cognitive_fallback": False,
    }
    payload.update(overrides)
    return payload


async def _request(
    app: FastAPI,
    *,
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> tuple[int, dict[str, object]]:
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
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (name.lower().encode(), value.encode())
            for name, value in (headers or {}).items()
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    await app(scope, receive, cast(Any, send))

    start = next(
        message
        for message in messages
        if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        cast(bytes, message.get("body", b""))
        for message in messages
        if message["type"] == "http.response.body"
    )
    decoded = json.loads(response_body)
    assert isinstance(decoded, dict)
    return cast(int, start["status"]), decoded


async def _post(
    app: FastAPI,
    payload: object,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    request_headers = (
        {"content-type": "application/json"}
        if headers is None
        else dict(headers)
    )
    return await _request(
        app,
        method="POST",
        path="/local/command",
        headers=request_headers,
        body=json.dumps(payload).encode(),
    )


def _strict_headers(
    csrf_token: str,
    *,
    content_type: str = "application/json",
) -> dict[str, str]:
    return {
        "host": INTERACTIVE_HOST,
        "origin": INTERACTIVE_ORIGIN,
        "content-type": content_type,
        "x-luxiom-csrf": csrf_token,
    }


class RecordingRuntime:
    def __init__(self, *, start_error: Exception | None = None) -> None:
        self.calls: list[str] = []
        self.gateway = LocalCommandApplicationGateway(object())
        self.csrf_token = "recording-runtime-csrf-token"
        self.start_error = start_error

    def start(self) -> None:
        self.calls.append("start")
        if self.start_error is not None:
            raise self.start_error

    def close(self) -> None:
        self.calls.append("close")


def test_factory_is_no_io_keeps_runtime_new_and_builds_separate_surface(
    tmp_path: Path,
) -> None:
    from app.api.interactive import create_local_interactive_app
    from app.main import app as default_app

    database_path = tmp_path / "interactive.sqlite3"
    runtime = LocalInteractiveRuntime(database_path, TEST_PROOF)

    app = create_local_interactive_app(runtime)

    assert type(app) is FastAPI
    assert app is not default_app
    assert runtime.state is LocalInteractiveRuntimeState.NEW
    assert not database_path.exists()
    assert not hasattr(app.state, _STATE_GATEWAY)
    luxiom_paths = {
        path: tuple(sorted(methods))
        for path, methods in app.openapi()["paths"].items()
        if path.startswith(("/local", "/brain", "/knowledge"))
        or path == "/health"
    }
    assert luxiom_paths == {("/local/command"): ("post",)}


def test_lifespan_starts_once_injects_exact_gateway_and_cleans_up() -> None:
    from app.api.interactive import create_local_interactive_app

    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)

    async def exercise() -> None:
        assert not hasattr(app.state, _STATE_GATEWAY)
        async with app.router.lifespan_context(app):
            assert runtime.calls == ["start"]
            assert getattr(app.state, _STATE_GATEWAY) is runtime.gateway
        assert not hasattr(app.state, _STATE_GATEWAY)

    asyncio.run(exercise())
    assert runtime.calls == ["start", "close"]


def test_failed_startup_closes_without_gateway_or_request_serving() -> None:
    from app.api.interactive import create_local_interactive_app

    runtime = RecordingRuntime(
        start_error=LocalInteractiveRuntimeError("sanitized startup failure")
    )
    app = create_local_interactive_app(runtime)
    yielded = False

    async def exercise() -> None:
        nonlocal yielded
        with pytest.raises(LocalInteractiveRuntimeError, match="sanitized"):
            async with app.router.lifespan_context(app):
                yielded = True

    asyncio.run(exercise())
    assert yielded is False
    assert runtime.calls == ["start", "close"]
    assert not hasattr(app.state, _STATE_GATEWAY)


def test_explicit_valid_gateway_wins_and_executes_exactly_once(monkeypatch) -> None:
    injected = LocalCommandApplicationGateway(object())
    calls: list[LocalCommandApplicationGateway] = []

    def execute(self, request):
        del request
        calls.append(self)
        if self is not injected:
            raise AssertionError("Default gateway must not execute.")
        return LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="injected result",
        )

    monkeypatch.setattr(LocalCommandApplicationGateway, "execute", execute)
    app = FastAPI()
    app.state.local_command_application_gateway = injected
    app.include_router(local_command.router)

    status, response = asyncio.run(_post(app, _payload()))

    assert status == 200
    assert response["response"] == "injected result"
    assert calls == [injected]


def test_absent_injection_uses_historical_default_exactly_once(monkeypatch) -> None:
    default = local_command.container.local_command_application_gateway
    calls: list[LocalCommandApplicationGateway] = []

    def execute(self, request):
        del request
        calls.append(self)
        return LocalCommandApplicationResult(
            False,
            error=local_command.application_error(
                local_command.LocalCommandApplicationErrorCode.ACCESS_DENIED
            ),
        )

    monkeypatch.setattr(LocalCommandApplicationGateway, "execute", execute)
    app = FastAPI()
    app.include_router(local_command.router)

    status, response = asyncio.run(_post(app, _payload()))

    assert status == 403
    assert response["error"]["code"] == "access_denied"
    assert calls == [default]


@pytest.mark.parametrize("invalid_gateway", (None, object()))
def test_invalid_explicit_injection_fails_closed_without_fallback(
    monkeypatch,
    invalid_gateway: object,
) -> None:
    calls = []

    def execute(self, request):
        calls.append((self, request))
        raise AssertionError("Default gateway must not execute.")

    monkeypatch.setattr(LocalCommandApplicationGateway, "execute", execute)
    app = FastAPI()
    app.state.local_command_application_gateway = invalid_gateway
    app.include_router(local_command.router)

    status, response = asyncio.run(_post(app, _payload()))

    assert status == 500
    assert response == {
        "success": False,
        "route": None,
        "response": None,
        "error": {
            "code": "internal_error",
            "message": "The request could not be completed.",
        },
    }
    assert calls == []


def test_real_runtime_http_add_read_wrong_proof_and_shutdown(
    tmp_path: Path,
) -> None:
    from app.api.interactive import create_local_interactive_app
    from app.core.container import container as default_container

    default_identity = id(default_container)
    runtime = LocalInteractiveRuntime(tmp_path / "interactive.sqlite3", TEST_PROOF)
    app = create_local_interactive_app(runtime)

    async def exercise() -> None:
        async with app.router.lifespan_context(app):
            assert app.state.local_command_application_gateway is runtime.gateway

            add_status, add = await _post(
                app,
                _payload(text="list add sprint34-b2 :: alpha | beta"),
                headers=_strict_headers(runtime.csrf_token),
            )
            assert add_status == 200
            assert add == {
                "success": True,
                "route": "local",
                "response": "List updated locally.",
                "error": None,
                "projection": {
                    "kind": "list",
                    "operation": "add",
                    "list_id": "sprint34-b2",
                    "added": ["alpha", "beta"],
                    "already_present": [],
                    "items": ["alpha", "beta"],
                },
            }

            read_status, read = await _post(
                app,
                _payload(text="list read sprint34-b2"),
                headers=_strict_headers(runtime.csrf_token),
            )
            assert read_status == 200
            assert read == {
                "success": True,
                "route": "local",
                "response": "List read locally.",
                "error": None,
                "projection": {
                    "kind": "list",
                    "operation": "read",
                    "list_id": "sprint34-b2",
                    "items": ["alpha", "beta"],
                },
            }

            proof = "wrong-proof-that-must-not-leak"
            denied_status, denied = await _post(
                app,
                _payload(proof=proof),
                headers=_strict_headers(runtime.csrf_token),
            )
            assert denied_status == 403
            assert denied["error"]["code"] == "access_denied"
            assert "projection" not in denied
            assert proof not in json.dumps(denied)

    asyncio.run(exercise())
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED
    assert not hasattr(app.state, _STATE_GATEWAY)
    assert id(default_container) == default_identity


def test_public_results_allow_only_closed_projection_not_generic_payloads() -> None:
    application_fields = {
        field.name for field in fields(LocalCommandApplicationResult)
    }
    http_fields = set(LocalCommandHttpResponse.model_fields)
    prohibited = {
        "payload",
        "data",
        "items",
        "records",
        "metadata",
        "result_details",
    }

    assert application_fields == {
        "success",
        "route",
        "response",
        "error",
        "projection",
    }
    assert http_fields == {
        "success",
        "route",
        "response",
        "error",
        "projection",
    }
    assert application_fields.isdisjoint(prohibited)
    assert http_fields.isdisjoint(prohibited)


_TRANSPORT_REJECTION = {
    "success": False,
    "route": None,
    "response": None,
    "error": {
        "code": "local_transport_rejected",
        "message": "The local request was rejected.",
    },
}


@pytest.mark.parametrize(
    "host",
    (
        None,
        "localhost:8765",
        "127.0.0.1",
        "127.0.0.1:8000",
        "[::1]:8765",
        "evil.example",
        "127.0.0.1:8765.evil.example",
    ),
)
def test_interactive_host_is_exact_and_rejects_before_gateway(
    monkeypatch,
    host: str | None,
) -> None:
    from app.api.interactive import create_local_interactive_app

    calls = []

    def execute(self, request):
        calls.append((self, request))
        raise AssertionError("Rejected transport must not execute the gateway.")

    monkeypatch.setattr(LocalCommandApplicationGateway, "execute", execute)
    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)
    headers = _strict_headers(runtime.csrf_token)
    if host is None:
        del headers["host"]
    else:
        headers["host"] = host

    async def exercise() -> tuple[int, dict[str, object]]:
        async with app.router.lifespan_context(app):
            return await _post(app, _payload(), headers=headers)

    status, response = asyncio.run(exercise())
    assert status == 400
    assert response == _TRANSPORT_REJECTION
    assert calls == []


@pytest.mark.parametrize(
    "origin",
    (
        None,
        "http://localhost:8765",
        "https://127.0.0.1:8765",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "null",
    ),
)
def test_interactive_origin_is_exact_and_rejects_before_gateway(
    monkeypatch,
    origin: str | None,
) -> None:
    from app.api.interactive import create_local_interactive_app

    calls = []
    monkeypatch.setattr(
        LocalCommandApplicationGateway,
        "execute",
        lambda self, request: calls.append((self, request)),
    )
    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)
    headers = _strict_headers(runtime.csrf_token)
    if origin is None:
        del headers["origin"]
    else:
        headers["origin"] = origin

    async def exercise() -> tuple[int, dict[str, object]]:
        async with app.router.lifespan_context(app):
            return await _post(app, _payload(), headers=headers)

    status, response = asyncio.run(exercise())
    assert status == 403
    assert response == _TRANSPORT_REJECTION
    assert calls == []


@pytest.mark.parametrize(
    "content_type",
    (
        "application/json",
        "APPLICATION/JSON",
        " application/json ",
        "application/json; charset=utf-8",
        "application/json;charset=utf-8",
        "application/json ; charset=utf-8",
        "application/json;CHARSET=UTF-8",
        "application/json ; CHARSET = UTF-8",
    ),
)
def test_interactive_accepts_only_frozen_json_content_types(
    monkeypatch,
    content_type: str,
) -> None:
    from app.api.interactive import create_local_interactive_app

    monkeypatch.setattr(
        LocalCommandApplicationGateway,
        "execute",
        lambda self, request: LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response="accepted",
        ),
    )
    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)

    async def exercise() -> tuple[int, dict[str, object]]:
        async with app.router.lifespan_context(app):
            return await _post(
                app,
                _payload(),
                headers=_strict_headers(
                    runtime.csrf_token,
                    content_type=content_type,
                ),
            )

    status, response = asyncio.run(exercise())
    assert status == 200
    assert response["response"] == "accepted"


@pytest.mark.parametrize(
    "content_type",
    (
        None,
        "text/json",
        "text/plain",
        "application/json; charset=latin-1",
        "application/json; charset=utf-8; foo=bar",
        "application/json; foo=bar",
        "application/json; charset=utf-8; charset=utf-8",
        "application/json-patch+json",
    ),
)
def test_interactive_rejects_unsupported_content_types_before_gateway(
    monkeypatch,
    content_type: str | None,
) -> None:
    from app.api.interactive import create_local_interactive_app

    calls = []
    monkeypatch.setattr(
        LocalCommandApplicationGateway,
        "execute",
        lambda self, request: calls.append((self, request)),
    )
    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)
    headers = _strict_headers(runtime.csrf_token)
    if content_type is None:
        del headers["content-type"]
    else:
        headers["content-type"] = content_type

    async def exercise() -> tuple[int, dict[str, object]]:
        async with app.router.lifespan_context(app):
            return await _post(app, _payload(), headers=headers)

    status, response = asyncio.run(exercise())
    assert status == 415
    assert response == _TRANSPORT_REJECTION
    assert calls == []


@pytest.mark.parametrize("csrf", (None, "wrong-csrf-token"))
def test_interactive_rejects_missing_or_wrong_csrf_without_disclosure(
    monkeypatch,
    csrf: str | None,
) -> None:
    from app.api.interactive import create_local_interactive_app

    calls = []
    monkeypatch.setattr(
        LocalCommandApplicationGateway,
        "execute",
        lambda self, request: calls.append((self, request)),
    )
    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)
    headers = _strict_headers(runtime.csrf_token)
    if csrf is None:
        del headers["x-luxiom-csrf"]
    else:
        headers["x-luxiom-csrf"] = csrf

    async def exercise() -> tuple[int, dict[str, object]]:
        async with app.router.lifespan_context(app):
            return await _post(app, _payload(), headers=headers)

    status, response = asyncio.run(exercise())
    assert status == 403
    assert response == _TRANSPORT_REJECTION
    assert runtime.csrf_token not in json.dumps(response)
    assert calls == []


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    (
        ({}, 400),
        ({"host": INTERACTIVE_HOST}, 403),
        (
            {"host": INTERACTIVE_HOST, "origin": INTERACTIVE_ORIGIN},
            415,
        ),
        (
            {
                "host": INTERACTIVE_HOST,
                "origin": INTERACTIVE_ORIGIN,
                "content-type": "application/json",
            },
            403,
        ),
    ),
)
def test_transport_validation_order_precedes_malformed_body(
    headers: dict[str, str],
    expected_status: int,
) -> None:
    from app.api.interactive import create_local_interactive_app

    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)

    async def exercise() -> tuple[int, dict[str, object]]:
        async with app.router.lifespan_context(app):
            return await _request(
                app,
                method="POST",
                path="/local/command",
                headers=headers,
                body=b"not-json",
            )

    status, response = asyncio.run(exercise())
    assert status == expected_status
    assert response == _TRANSPORT_REJECTION


def test_host_policy_precedes_unknown_route_but_valid_host_reaches_404() -> None:
    from app.api.interactive import create_local_interactive_app

    runtime = RecordingRuntime()
    app = create_local_interactive_app(runtime)

    async def exercise() -> tuple[
        tuple[int, dict[str, object]],
        tuple[int, dict[str, object]],
    ]:
        async with app.router.lifespan_context(app):
            rejected = await _request(
                app,
                method="GET",
                path="/unknown",
                headers={"host": "localhost:8765"},
            )
            routed = await _request(
                app,
                method="GET",
                path="/unknown",
                headers={"host": INTERACTIVE_HOST},
            )
            return rejected, routed

    rejected, routed = asyncio.run(exercise())
    assert rejected == (400, _TRANSPORT_REJECTION)
    assert routed[0] == 404
    assert routed[1]["detail"] == "Not Found"


def test_historical_app_has_no_interactive_transport_policy() -> None:
    from app.main import app as default_app

    status, response = asyncio.run(
        _post(
            default_app,
            _payload(proof="wrong-proof"),
            headers={"host": "testserver"},
        )
    )

    assert status == 403
    assert response["error"]["code"] == "access_denied"


def test_interactive_app_has_no_cors_middleware() -> None:
    from app.api.interactive import create_local_interactive_app

    app = create_local_interactive_app(RecordingRuntime())

    assert all(
        middleware.cls.__name__ != "CORSMiddleware"
        for middleware in app.user_middleware
    )
