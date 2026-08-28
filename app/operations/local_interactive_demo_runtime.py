"""Operations-only proof composition for the local interactive runtime.

The fixed proof below is development/operations demonstration material only,
not a production credential. It is never persisted, printed, or transferred.
"""

from __future__ import annotations

import asyncio
import json
from html.parser import HTMLParser
from pathlib import Path
from types import TracebackType
from typing import Any, cast

from fastapi import FastAPI

from app.api.interactive import create_local_interactive_app
from app.cognition.local_resolution.permissions import LIST_ITEMS_READ
from app.infrastructure.local_storage.sqlite_storage import (
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
)
from app.membership.models import MembershipStatus
from app.operations.local_interactive_runtime import (
    DEVELOPMENT_ACTOR,
    DEVELOPMENT_WORKSPACE,
    LocalInteractiveRuntime,
    LocalInteractiveRuntimeState,
)

DEMO_PROOF = "luxiom-sprint34-operations-demonstration"
DEMO_WORKSPACE = DEVELOPMENT_WORKSPACE
BASE_URL = "http://127.0.0.1:8765"

DURABILITY_ADD = "list add sprint34-durability-proof :: alpha | beta"
DURABILITY_READ = "list read sprint34-durability-proof"
MEMBERSHIP_READ = "list read sprint34-membership-denial"
PERMISSION_READ = "list read sprint34-permission-denial"

ADD_SUCCESS = {
    "success": True,
    "route": "local",
    "response": "List updated locally.",
    "error": None,
}
READ_SUCCESS = {
    "success": True,
    "route": "local",
    "response": "List read locally.",
    "error": None,
}
MEMBERSHIP_DENIAL = {
    "success": False,
    "route": None,
    "response": None,
    "error": {"code": "access_denied", "message": "Access denied."},
}
PERMISSION_DENIAL = {
    "success": False,
    "route": "local",
    "response": None,
    "error": {
        "code": "local_permission_denied",
        "message": "The local operation is not permitted.",
    },
}


class DemoOperationalError(RuntimeError):
    """Represent a sanitized failure in the operations demonstration."""


_HISTORICAL_RESPONSE_FIELDS = (
    "success",
    "route",
    "response",
    "error",
)
_HISTORICAL_RESPONSE_FIELD_SET = frozenset(_HISTORICAL_RESPONSE_FIELDS)
_ALLOWED_DEMO_RESPONSE_FIELDS = (
    _HISTORICAL_RESPONSE_FIELD_SET | frozenset({"projection"})
)


def _historical_demo_response(
    response: dict[str, object],
) -> dict[str, object]:
    """Extract the immutable Sprint 34 envelope from an additive HTTP result."""

    fields = frozenset(response)

    if (
        not _HISTORICAL_RESPONSE_FIELD_SET.issubset(fields)
        or not fields.issubset(_ALLOWED_DEMO_RESPONSE_FIELDS)
    ):
        raise DemoOperationalError(
            "The demonstration response is invalid."
        )

    return {
        field: response[field]
        for field in _HISTORICAL_RESPONSE_FIELDS
    }


class _CsrfParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tokens: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        if tag == "meta" and values.get("name") == "luxiom-csrf":
            token = values.get("content")
            if token:
                self.tokens.append(token)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_demo_database(database_path: str | Path, repository: Path) -> Path:
    supplied = Path(database_path)
    candidate = supplied.resolve(strict=False)
    root = repository.resolve(strict=False)
    if (
        not supplied.is_absolute()
        or candidate == root
        or root in candidate.parents
        or candidate.name in {"", ".", ".."}
        or candidate.is_dir()
    ):
        raise DemoOperationalError("The demonstration database is unavailable.")
    return candidate


async def _asgi_request(
    app: FastAPI,
    *,
    method: str,
    path: str,
    headers: dict[str, str],
    body: bytes = b"",
) -> tuple[int, bytes]:
    messages: list[dict[str, object]] = []
    request_sent = False

    async def receive() -> dict[str, object]:
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
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
        "headers": [
            (name.lower().encode(), value.encode())
            for name, value in headers.items()
        ],
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8765),
    }
    await app(cast(Any, scope), receive, cast(Any, send))
    start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        cast(bytes, message.get("body", b""))
        for message in messages
        if message["type"] == "http.response.body"
    )
    return cast(int, start["status"]), response_body


async def _delivered_csrf(app: FastAPI) -> str:
    status, body = await _asgi_request(
        app,
        method="GET",
        path="/local/ui",
        headers={"host": "127.0.0.1:8765"},
    )
    if status != 200:
        raise DemoOperationalError("The demonstration UI is unavailable.")
    parser = _CsrfParser()
    parser.feed(body.decode())
    if len(parser.tokens) != 1:
        raise DemoOperationalError("The demonstration UI is unavailable.")
    return parser.tokens[0]


class DemoInteractiveSession:
    """Own one actual interactive app lifespan for an operations proof phase."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = validate_demo_database(database_path, _repository_root())
        self.runtime = LocalInteractiveRuntime(self.database_path, DEMO_PROOF)
        self.app = create_local_interactive_app(self.runtime)
        self._runner = asyncio.Runner()
        self._lifespan = self.app.router.lifespan_context(self.app)
        self._csrf: str | None = None
        self.csrf_source: str | None = None

    def __enter__(self) -> DemoInteractiveSession:
        self._runner.run(self._lifespan.__aenter__())
        self._csrf = self._runner.run(_delivered_csrf(self.app))
        self.csrf_source = "GET /local/ui"
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._csrf = None
        self._runner.run(self._lifespan.__aexit__(exc_type, exc_value, traceback))
        self._runner.close()

    def __repr__(self) -> str:
        return f"DemoInteractiveSession(database_path={self.database_path!r})"

    @staticmethod
    def payload(text: str) -> dict[str, object]:
        return {
            "proof": DEMO_PROOF,
            "requested_workspace_id": DEMO_WORKSPACE.workspace_id,
            "text": text,
            "allow_cognitive_fallback": False,
        }

    def post(self, text: str) -> tuple[int, dict[str, object]]:
        if not self._csrf:
            raise DemoOperationalError("The demonstration session is unavailable.")
        status, response_body = self._runner.run(
            _asgi_request(
                self.app,
                method="POST",
                path="/local/command",
                body=json.dumps(self.payload(text)).encode(),
                headers={
                    "host": "127.0.0.1:8765",
                    "origin": BASE_URL,
                    "content-type": "application/json",
                    "x-luxiom-csrf": self._csrf,
                },
            )
        )
        decoded = json.loads(response_body)
        if not isinstance(decoded, dict):
            raise DemoOperationalError("The demonstration response is invalid.")
        return status, decoded


def _open_storage(database_path: Path) -> SQLiteLocalStorage:
    storage = SQLiteLocalStorage(database_path)
    storage.open()
    storage.initialize()
    return storage


def deactivate_demo_membership(database_path: Path) -> None:
    storage = _open_storage(database_path)
    try:
        membership = storage.deactivate(DEVELOPMENT_ACTOR, DEMO_WORKSPACE)
        if membership is None or membership.status is not MembershipStatus.INACTIVE:
            raise DemoOperationalError("Membership fixture preparation failed.")
    finally:
        storage.close()


def revoke_demo_read_permission(database_path: Path) -> None:
    storage = _open_storage(database_path)
    try:
        membership = storage.get(DEVELOPMENT_ACTOR, DEMO_WORKSPACE)
        if membership is None or membership.status is not MembershipStatus.ACTIVE:
            raise DemoOperationalError("Permission fixture preparation failed.")
        permissions = SQLitePermissionGrantRepository(storage)
        permissions.revoke(DEVELOPMENT_ACTOR, DEMO_WORKSPACE, LIST_ITEMS_READ)
        if permissions.is_granted(DEVELOPMENT_ACTOR, DEMO_WORKSPACE, LIST_ITEMS_READ):
            raise DemoOperationalError("Permission fixture preparation failed.")
    finally:
        storage.close()


def observe_durable_items(database_path: Path) -> tuple[str, ...]:
    storage = _open_storage(database_path)
    try:
        return storage.read(DEMO_WORKSPACE, "sprint34-durability-proof").items
    finally:
        storage.close()


def run_durability_write(database_path: str | Path) -> dict[str, object]:
    with DemoInteractiveSession(database_path) as session:
        status, response = session.post(DURABILITY_ADD)
        historical_response = _historical_demo_response(response)
        if status != 200 or historical_response != ADD_SUCCESS:
            raise DemoOperationalError("Durability HTTP write failed.")
    if session.runtime.state is not LocalInteractiveRuntimeState.CLOSED:
        raise DemoOperationalError("Durability runtime cleanup failed.")
    return historical_response


def run_durability_read_and_observe(
    database_path: str | Path,
) -> tuple[dict[str, object], tuple[str, ...]]:
    path = validate_demo_database(database_path, _repository_root())
    with DemoInteractiveSession(path) as session:
        status, response = session.post(DURABILITY_READ)
        historical_response = _historical_demo_response(response)
        if status != 200 or historical_response != READ_SUCCESS:
            raise DemoOperationalError("Durability HTTP read failed.")
    if session.runtime.state is not LocalInteractiveRuntimeState.CLOSED:
        raise DemoOperationalError("Durability runtime cleanup failed.")
    items = observe_durable_items(path)
    if items != ("alpha", "beta"):
        raise DemoOperationalError("Durability observation failed.")
    return historical_response, items


def run_membership_denial(
    database_path: str | Path,
) -> tuple[int, dict[str, object]]:
    path = validate_demo_database(database_path, _repository_root())
    with DemoInteractiveSession(path) as session:
        deactivate_demo_membership(path)
        result = session.post(MEMBERSHIP_READ)
        if result != (403, MEMBERSHIP_DENIAL):
            raise DemoOperationalError("Membership denial proof failed.")
        return result


def run_permission_denial(
    database_path: str | Path,
) -> tuple[int, dict[str, object]]:
    path = validate_demo_database(database_path, _repository_root())
    with DemoInteractiveSession(path) as session:
        revoke_demo_read_permission(path)
        result = session.post(PERMISSION_READ)
        if result != (403, PERMISSION_DENIAL):
            raise DemoOperationalError("Permission denial proof failed.")
        return result
