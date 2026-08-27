import asyncio
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI

from app.api.interactive import create_local_interactive_app
from app.operations.local_interactive_runtime import (
    DEVELOPMENT_WORKSPACE,
    LocalInteractiveRuntime,
    LocalInteractiveRuntimeState,
)

HOST = "127.0.0.1:8765"
ORIGIN = "http://127.0.0.1:8765"
TEST_PROOF = "sprint34-b4-test-proof"
ASSET_ROOT = Path("app/api/static/local_ui")
EXPECTED_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "img-src 'self'; connect-src 'self'; font-src 'none'; "
    "object-src 'none'; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'none';"
)
TRANSPORT_REJECTION = {
    "success": False,
    "route": None,
    "response": None,
    "error": {
        "code": "local_transport_rejected",
        "message": "The local request was rejected.",
    },
}


async def _request(
    app: FastAPI,
    *,
    method: str,
    path: str,
    headers: list[tuple[bytes, bytes]],
    body: bytes = b"",
) -> tuple[int, dict[str, str], bytes]:
    messages: list[dict[str, object]] = []
    sent = False

    async def receive() -> dict[str, object]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

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
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("127.0.0.1", 8765),
    }
    await app(scope, receive, cast(Any, send))
    start = next(
        message
        for message in messages
        if message["type"] == "http.response.start"
    )
    response_headers = {
        cast(bytes, name).decode().lower(): cast(bytes, value).decode()
        for name, value in cast(list[tuple[bytes, bytes]], start["headers"])
    }
    response_body = b"".join(
        cast(bytes, message.get("body", b""))
        for message in messages
        if message["type"] == "http.response.body"
    )
    return cast(int, start["status"]), response_headers, response_body


def _get(
    app: FastAPI,
    path: str,
    *,
    host: str = HOST,
) -> tuple[int, dict[str, str], bytes]:
    return asyncio.run(
        _request(
            app,
            method="GET",
            path=path,
            headers=[(b"host", host.encode())],
        )
    )


async def _post(
    app: FastAPI,
    *,
    proof: str,
    text: str,
    csrf: str,
) -> tuple[int, dict[str, object]]:
    payload = {
        "proof": proof,
        "requested_workspace_id": DEVELOPMENT_WORKSPACE.workspace_id,
        "text": text,
        "allow_cognitive_fallback": False,
    }
    status, _, body = await _request(
        app,
        method="POST",
        path="/local/command",
        headers=[
            (b"host", HOST.encode()),
            (b"origin", ORIGIN.encode()),
            (b"content-type", b"application/json"),
            (b"x-luxiom-csrf", csrf.encode()),
        ],
        body=json.dumps(payload).encode(),
    )
    decoded = json.loads(body)
    assert isinstance(decoded, dict)
    return status, decoded


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.csrf_values: list[str] = []
        self.scripts: list[dict[str, str | None]] = []
        self.stylesheets: list[str] = []
        self.inputs: list[dict[str, str | None]] = []
        self.textareas: list[dict[str, str | None]] = []
        self.buttons: list[dict[str, str | None]] = []
        self.inline_styles = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        if values.get("style") is not None:
            self.inline_styles += 1
        if tag == "meta" and values.get("name") == "luxiom-csrf":
            self.csrf_values.append(values.get("content") or "")
        if tag == "script":
            self.scripts.append(values)
        if tag == "style":
            self.inline_styles += 1
        if tag == "link" and values.get("rel") == "stylesheet":
            self.stylesheets.append(values.get("href") or "")
        if tag == "input":
            self.inputs.append(values)
        if tag == "textarea":
            self.textareas.append(values)
        if tag == "button":
            self.buttons.append(values)


def _parse(document: str) -> _DocumentParser:
    parser = _DocumentParser()
    parser.feed(document)
    return parser


def test_ui_html_delivers_one_runtime_csrf_with_frozen_headers(
    tmp_path: Path,
) -> None:
    runtime = LocalInteractiveRuntime(tmp_path / "ui.sqlite3", TEST_PROOF)
    app = create_local_interactive_app(runtime)

    async def exercise() -> tuple[int, dict[str, str], bytes, str]:
        async with app.router.lifespan_context(app):
            status, headers, body = await _request(
                app,
                method="GET",
                path="/local/ui",
                headers=[(b"host", HOST.encode())],
            )
            return status, headers, body, runtime.csrf_token

    status, headers, body, token = asyncio.run(exercise())
    document = body.decode()
    parsed = _parse(document)

    assert status == 200
    assert headers["content-type"].startswith("text/html")
    assert headers["cache-control"] == "no-store"
    assert headers["content-security-policy"] == EXPECTED_CSP
    assert parsed.csrf_values == [token]
    assert document.count(token) == 1
    assert runtime.state is LocalInteractiveRuntimeState.CLOSED


@pytest.mark.parametrize(
    ("path", "media_type"),
    (
        ("/local/ui/styles.css", "text/css"),
        ("/local/ui/app.js", "javascript"),
    ),
)
def test_known_static_routes_are_local_host_only(
    tmp_path: Path,
    path: str,
    media_type: str,
) -> None:
    runtime = LocalInteractiveRuntime(tmp_path / "assets.sqlite3", TEST_PROOF)
    app = create_local_interactive_app(runtime)

    async def exercise():
        async with app.router.lifespan_context(app):
            valid = await _request(
                app,
                method="GET",
                path=path,
                headers=[(b"host", HOST.encode())],
            )
            invalid = await _request(
                app,
                method="GET",
                path=path,
                headers=[(b"host", b"localhost:8765")],
            )
            return valid, invalid

    valid, invalid = asyncio.run(exercise())
    assert valid[0] == 200
    assert media_type in valid[1]["content-type"]
    assert invalid[0] == 400
    assert json.loads(invalid[2]) == TRANSPORT_REJECTION


def test_ui_document_is_csp_compatible_and_has_minimal_controls(
    tmp_path: Path,
) -> None:
    runtime = LocalInteractiveRuntime(tmp_path / "document.sqlite3", TEST_PROOF)
    app = create_local_interactive_app(runtime)

    async def exercise() -> str:
        async with app.router.lifespan_context(app):
            _, _, body = await _request(
                app,
                method="GET",
                path="/local/ui",
                headers=[(b"host", HOST.encode())],
            )
            return body.decode()

    document = asyncio.run(exercise())
    parsed = _parse(document)
    proof = next(item for item in parsed.inputs if item.get("id") == "proof")
    fallback = next(
        item for item in parsed.inputs if item.get("id") == "cognitive-fallback"
    )

    assert parsed.stylesheets == ["/local/ui/styles.css"]
    assert parsed.scripts == [{"src": "/local/ui/app.js", "defer": None}]
    assert parsed.inline_styles == 0
    assert proof.get("type") == "password"
    assert proof.get("autocomplete") == "off"
    assert proof.get("value") is None
    assert fallback.get("type") == "checkbox"
    assert "checked" not in fallback
    assert any(item.get("id") == "command" for item in parsed.textareas)
    assert any(item.get("type") == "submit" for item in parsed.buttons)
    assert "http://" not in document
    assert "https://" not in document


def test_static_sources_follow_browser_security_contract() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    css = (ASSET_ROOT / "styles.css").read_text(encoding="utf-8")
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")

    assert html.count("__LUXIOM_CSRF_TOKEN__") == 1
    assert TEST_PROOF not in html + css + script
    assert "luxiom-local-dev-workspace" in script
    assert 'document.querySelector("meta[name=\\"luxiom-csrf\\"]")' in script
    assert '"X-Luxiom-CSRF": csrfToken' in script
    assert '"Content-Type": "application/json"' in script
    assert 'fetch("/local/command"' in script
    assert "allow_cognitive_fallback: fallbackInput.checked" in script
    assert script.index("JSON.stringify") < script.index('proofInput.value = ""')
    assert script.index('proofInput.value = ""') < script.index("fetch(")
    assert ".textContent" in script

    forbidden = (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "new Function",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "document.cookie",
        "serviceWorker",
        "http://",
        "https://",
    )
    assert all(value not in html + css + script for value in forbidden)
    assert "console." not in script


def test_no_generic_static_path_or_extra_ui_endpoint(tmp_path: Path) -> None:
    runtime = LocalInteractiveRuntime(tmp_path / "routes.sqlite3", TEST_PROOF)
    app = create_local_interactive_app(runtime)

    async def exercise() -> tuple[int, int]:
        async with app.router.lifespan_context(app):
            traversal = await _request(
                app,
                method="GET",
                path="/local/ui/../secret.txt",
                headers=[(b"host", HOST.encode())],
            )
            token_endpoint = await _request(
                app,
                method="GET",
                path="/local/ui/token",
                headers=[(b"host", HOST.encode())],
            )
            return traversal[0], token_endpoint[0]

    assert asyncio.run(exercise()) == (404, 404)


def test_delivered_token_drives_real_add_read_and_auth_boundaries(
    tmp_path: Path,
) -> None:
    runtime = LocalInteractiveRuntime(tmp_path / "flow.sqlite3", TEST_PROOF)
    app = create_local_interactive_app(runtime)

    async def exercise():
        async with app.router.lifespan_context(app):
            _, _, html = await _request(
                app,
                method="GET",
                path="/local/ui",
                headers=[(b"host", HOST.encode())],
            )
            tokens = _parse(html.decode()).csrf_values
            assert len(tokens) == 1
            token = tokens[0]
            add = await _post(
                app,
                proof=TEST_PROOF,
                text="list add sprint34-b4 :: alpha | beta",
                csrf=token,
            )
            read = await _post(
                app,
                proof=TEST_PROOF,
                text="list read sprint34-b4",
                csrf=token,
            )
            wrong_proof = await _post(
                app,
                proof="wrong-proof",
                text="list read sprint34-b4",
                csrf=token,
            )
            wrong_csrf = await _post(
                app,
                proof=TEST_PROOF,
                text="list read sprint34-b4",
                csrf="wrong-csrf",
            )
            return add, read, wrong_proof, wrong_csrf

    add, read, wrong_proof, wrong_csrf = asyncio.run(exercise())
    assert add == (
        200,
        {
            "success": True,
            "route": "local",
            "response": "List updated locally.",
            "error": None,
        },
    )
    assert read == (
        200,
        {
            "success": True,
            "route": "local",
            "response": "List read locally.",
            "error": None,
        },
    )
    assert wrong_proof[0] == 403
    assert wrong_proof[1]["error"]["code"] == "access_denied"
    assert wrong_csrf == (403, TRANSPORT_REJECTION)


def test_fresh_runtime_rotates_token_and_rejects_old_token(tmp_path: Path) -> None:
    first = LocalInteractiveRuntime(tmp_path / "first.sqlite3", TEST_PROOF)
    second = LocalInteractiveRuntime(tmp_path / "second.sqlite3", TEST_PROOF)
    first_app = create_local_interactive_app(first)
    second_app = create_local_interactive_app(second)

    async def token_from(app: FastAPI) -> str:
        _, _, body = await _request(
            app,
            method="GET",
            path="/local/ui",
            headers=[(b"host", HOST.encode())],
        )
        return _parse(body.decode()).csrf_values[0]

    async def exercise():
        async with first_app.router.lifespan_context(first_app):
            old_token = await token_from(first_app)
        async with second_app.router.lifespan_context(second_app):
            new_token = await token_from(second_app)
            rejected = await _post(
                second_app,
                proof=TEST_PROOF,
                text="list read sprint34-b4",
                csrf=old_token,
            )
            return old_token, new_token, rejected

    old_token, new_token, rejected = asyncio.run(exercise())
    assert old_token != new_token
    assert rejected == (403, TRANSPORT_REJECTION)
