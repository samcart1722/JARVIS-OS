"""Block D: independent ASGI transport and preparation authority proofs."""

import asyncio
import json
import logging

import pytest
from loguru import logger

from app.api.interactive import create_local_interactive_app
from app.cognition.intent_preparation.eligibility import assess_eligibility
from app.cognition.intent_preparation.models import EligibilityDecision
from app.infrastructure.local_storage.sqlite_storage import SQLiteLocalStorage
from app.local_command import LocalCommandApplicationGateway

PATH = "/local/intent-preparation"
HEADERS = [
    (b"host", b"127.0.0.1:8765"),
    (b"origin", b"http://127.0.0.1:8765"),
    (b"content-type", b"application/json"),
    (b"x-luxiom-csrf", b"block-D-csrf"),
]


class Runtime:
    csrf_token = "block-D-csrf"

    def __getattr__(self, name):
        pytest.fail(f"Preparation resolved forbidden runtime dependency: {name}")


class Provider:
    def __init__(self, data=None, error=None):
        self.data = data or '{"outcome":"unsupported","intent":null,"fields":{}}'
        self.error = error
        self.calls = []

    def prepare(self, text):
        self.calls.append(text)
        if self.error is not None:
            raise self.error
        return self.data


async def request(app, body, headers=HEADERS, path=PATH):
    events = []
    chunks = [body]
    reads = [0]

    async def receive():
        reads[0] += 1
        return (
            {"type": "http.request", "body": chunks.pop(), "more_body": False}
            if chunks
            else {"type": "http.disconnect"}
        )

    async def send(event):
        events.append(event)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": headers,
            "client": ("synthetic", 1),
            "server": ("127.0.0.1", 8765),
        },
        receive,
        send,
    )
    status = next(e["status"] for e in events if e["type"] == "http.response.start")
    raw = b"".join(
        e.get("body", b"") for e in events if e["type"] == "http.response.body"
    )
    app.state.block_d_body_reads = reads[0]
    return status, json.loads(raw)


@pytest.fixture
def guarded(monkeypatch):
    counts = {"authority": 0, "logs": 0}

    def authority(*args, **kwargs):
        counts["authority"] += 1
        pytest.fail("Preparation crossed execution/storage boundary")

    def logs(*args, **kwargs):
        counts["logs"] += 1
        pytest.fail("Preparation logged prompt/provider material")

    monkeypatch.setattr(LocalCommandApplicationGateway, "execute", authority)
    for name in (
        "open",
        "initialize",
        "add",
        "read",
        "store",
        "read_knowledge",
        "find_knowledge_by_key",
        "browse_knowledge",
        "get",
        "read_principal_actor_mapping",
        "is_permission_granted",
    ):
        monkeypatch.setattr(SQLiteLocalStorage, name, authority)
    monkeypatch.setattr(logging.Logger, "_log", logs)
    for name in (
        "trace",
        "debug",
        "info",
        "success",
        "warning",
        "error",
        "critical",
        "exception",
    ):
        monkeypatch.setattr(logger, name, logs)
    yield counts
    assert counts == {"authority": 0, "logs": 0}


@pytest.mark.parametrize(
    "name,status",
    [(b"host", 400), (b"origin", 403), (b"content-type", 415), (b"x-luxiom-csrf", 403)],
)
@pytest.mark.parametrize(
    "attack", ["missing", "wrong", "duplicate", "conflicting-duplicate"]
)
def test_transport_rejects_before_body_or_provider(guarded, name, status, attack):
    headers = [(n, v) for n, v in HEADERS if n != name]
    if attack != "missing":
        good = dict(HEADERS)[name]
        bad = b"invalid"
        headers.append((name.upper(), bad if attack == "wrong" else good))
        if "duplicate" in attack:
            headers.append((name, good if attack == "duplicate" else bad))
    provider = Provider(error=AssertionError("provider must not run"))
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=provider)
    # Invalid body would be 400 if middleware were bypassed.
    code, wire = asyncio.run(request(app, b"SECRET_INVALID_BODY", headers))
    assert code == status
    assert wire["error"]["code"] == "local_transport_rejected"
    assert provider.calls == []
    assert app.state.block_d_body_reads == 0


@pytest.mark.parametrize(
    "media",
    [
        b"text/plain",
        b"application/json;charset=latin-1",
        b"application/json; charset=utf-8; extra=x",
        b"application/json; charset=utf-16",
    ],
)
def test_media_rejection_is_pre_provider(guarded, media):
    p = Provider()
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=p)
    headers = [(n, media if n == b"content-type" else v) for n, v in HEADERS]
    assert asyncio.run(request(app, b'{"text":"Hola"}', headers))[0] == 415
    assert p.calls == []


PROTECTED = [
    "Recuerda que No entrega",
    "Recuerda que",
    "Qué sabes de K",
    "Agrega pan a mis pendientes",
    "knowledge malformed",
    "list malformed",
    "Nunca conserves X",
    "No conserves X",
    "Deja de conservar X",
    "Si conserva X",
    "Conserva X cuando Y",
    '"Conserva X"',
    "Por ejemplo: Conserva X",
    "Conserva X y agrega Y",
    "Conserva esto",
    "¿la lista Compras y la lista Hogar?",
]


@pytest.mark.parametrize("text", PROTECTED)
def test_independent_eligibility_precedes_provider_and_authority(guarded, text):
    assert assess_eligibility(text).decision is EligibilityDecision.PROTECTED
    p = Provider(error=AssertionError("protected input reached provider"))
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=p)
    assert asyncio.run(request(app, json.dumps({"text": text}).encode())) == (
        200,
        {"state": "unsupported", "candidate": None},
    )
    assert p.calls == []


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b"null",
        b"[]",
        b'{"text":42}',
        b'{"text":false}',
        b'{"text":{}}',
        b'{"text":"\\ud800"}',
        b'{"text":"Hola","eligible":true}',
        b'{"text":"Hola","reason":"safe_unrecognized"}',
        b'{"text":"Hola","model":"evil"}',
        b'{"text":"Hola","url":"https://evil.test"}',
        b'{"text":"Hola","proof":"authority"}',
        b'{"text":"Hola","text":"Hola"}',
        b'{"text":"Hola","te\\u0078t":"Hola"}',
        b'{"text":"Hola"} prose',
        b"\xff",
        json.dumps({"text": "x" * 8193}).encode(),
    ],
)
def test_closed_text_envelope_cannot_carry_authority_or_eligibility(guarded, body):
    p = Provider()
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=p)
    assert asyncio.run(request(app, body)) == (
        400,
        {"state": "unsupported", "candidate": None},
    )
    assert p.calls == []


@pytest.mark.parametrize(
    "media", [b"application/json", b"APPLICATION/JSON; CHARSET=UTF-8"]
)
def test_valid_transport_runs_once_without_authority_or_logs(guarded, media):
    text = "Conserva SECRET_LITERAL knowledge store :: <svg> café"
    fields = {"value": "SECRET_LITERAL knowledge store :: <svg> café"}
    p = Provider(
        json.dumps(
            {"outcome": "supported", "intent": "CAPTURE_KNOWLEDGE", "fields": fields}
        )
    )
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=p)
    headers = [(n.upper(), media if n == b"content-type" else v) for n, v in HEADERS]
    status, wire = asyncio.run(
        request(app, json.dumps({"text": text}).encode(), headers)
    )
    assert status == 200 and set(wire) == {"state", "candidate"}
    assert wire == {
        "state": "candidate_accepted",
        "candidate": {
            "intent": "CAPTURE_KNOWLEDGE",
            "fields": fields,
            "provenance": "local_model_assisted",
        },
    }
    assert p.calls == [text] and guarded == {"authority": 0, "logs": 0}


def test_public_surface_has_no_preparation_endpoint():
    from app.main import app

    assert PATH not in app.openapi()["paths"]


@pytest.mark.parametrize("unavailable", [False, True])
def test_eligible_provider_exceptions_are_closed_silent_and_non_authoritative(
    guarded, unavailable
):
    from app.cognition.intent_preparation.contracts import (
        PreparationProviderUnavailable,
    )

    error = (
        PreparationProviderUnavailable("SECRET_PROVIDER_MODEL")
        if unavailable
        else RuntimeError("SECRET_PROMPT_PROVIDER_EXCEPTION")
    )
    provider = Provider(error=error)
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=provider)
    assert asyncio.run(request(app, b'{"text":"Hola"}')) == (
        200,
        {
            "state": "provider_unavailable" if unavailable else "provider_failure",
            "candidate": None,
        },
    )
    assert provider.calls == ["Hola"]
    assert guarded == {"authority": 0, "logs": 0}
