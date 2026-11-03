"""ASGI-only local preparation tests: no sockets, models or authority I/O."""

import asyncio
import json

import pytest

from app.api.interactive import create_local_interactive_app
from app.cognition.intent_preparation.contracts import PreparationProviderUnavailable

PATH = "/local/intent-preparation"
HEADERS = [
    (b"host", b"127.0.0.1:8765"),
    (b"origin", b"http://127.0.0.1:8765"),
    (b"content-type", b"application/json"),
    (b"x-luxiom-csrf", b"synthetic-csrf"),
]


class Runtime:
    csrf_token = "synthetic-csrf"

    def start(self):
        pytest.fail("preparation must not bootstrap runtime")

    def close(self):
        pytest.fail("preparation must not close runtime")

    @property
    def gateway(self):
        pytest.fail("preparation must never resolve execution authority")


class Provider:
    def __init__(
        self, output='{"outcome":"unsupported","intent":null,"fields":{}}', error=None
    ):
        self.output, self.error = output, error
        self.calls = []

    def prepare(self, text):
        self.calls.append(text)
        if self.error:
            raise self.error
        return self.output


async def request(
    app, body=b'{"text":"Hola"}', headers=None, path=PATH, method="POST", chunks=None
):
    events = []
    pending = list(chunks) if chunks is not None else [body]

    async def receive():
        if not pending:
            return {"type": "http.disconnect"}
        data = pending.pop(0)
        return {"type": "http.request", "body": data, "more_body": bool(pending)}

    async def send(event):
        events.append(event)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "root_path": "",
            "headers": HEADERS if headers is None else headers,
            "client": ("synthetic", 1),
            "server": ("127.0.0.1", 8765),
        },
        receive,
        send,
    )
    status = next(e["status"] for e in events if e["type"] == "http.response.start")
    data = b"".join(
        e.get("body", b"") for e in events if e["type"] == "http.response.body"
    )
    return status, json.loads(data)


def post(provider, text="Hola", **kwargs):
    app = create_local_interactive_app(Runtime(), intent_preparation_provider=provider)
    kwargs.setdefault("body", json.dumps({"text": text}).encode())
    return asyncio.run(request(app, **kwargs))


@pytest.mark.parametrize(
    "text",
    [
        "Recuerda que cafe",
        "Qué sabes de K",
        "Agrega pan a mis pendientes",
        "Muéstrame la lista L",
        "No conserves cafe",
        "Nunca conserves cafe",
        '"Conserva cafe"',
        "Por ejemplo: Conserva cafe",
        "Conserva esto",
        "Conserva cafe si X",
        "Conserva cafe y agrega pan",
        "knowledge malformed",
        "list malformed",
        "¿la lista Compras y la lista Hogar?",
    ],
    ids=lambda value: type(value).__name__,
)
def test_direct_endpoint_recomputes_protected_eligibility_before_provider(text):
    provider = Provider(error=AssertionError("no call"))
    assert post(provider, text) == (200, {"state": "unsupported", "candidate": None})
    assert provider.calls == []


@pytest.mark.parametrize(
    "text,intent,fields",
    [
        ("Conserva café", "CAPTURE_KNOWLEDGE", {"value": "café"}),
        ("Busca Tema Ágil", "RECALL_KNOWLEDGE", {"key": "Tema Ágil"}),
        (
            "Incorpora pan a la lista Compras",
            "ADD_FOLLOW_UP",
            {"item": "pan", "list_id": "Compras"},
        ),
        ("Consulta la lista Compras", "READ_FOLLOW_UP", {"list_id": "Compras"}),
        ("Conserva café", "CAPTURE_KNOWLEDGE", {}),
    ],
    ids=lambda value: type(value).__name__,
)
def test_one_eligible_operation_returns_only_closed_semantic_data(text, intent, fields):
    provider = Provider(
        json.dumps({"outcome": "supported", "intent": intent, "fields": fields})
    )
    assert post(provider, text) == (
        200,
        {
            "state": "candidate_accepted",
            "candidate": {
                "intent": intent,
                "fields": fields,
                "provenance": "local_model_assisted",
            },
        },
    )
    assert provider.calls == [text]


@pytest.mark.parametrize(
    "name,wrong,status",
    [
        (b"host", b"localhost:8765", 400),
        (b"origin", b"http://evil.test", 403),
        (b"content-type", b"text/plain", 415),
        (b"x-luxiom-csrf", b"wrong", 403),
    ],
)
@pytest.mark.parametrize("variant", ["missing", "wrong", "duplicate"])
@pytest.mark.parametrize(
    "path", [PATH, "/local/command"], ids=lambda value: type(value).__name__
)
def test_strict_transport_preserves_both_routes(name, wrong, status, variant, path):
    provider = Provider(error=AssertionError("no call"))
    headers = [(n, v) for n, v in HEADERS if n != name]
    if variant == "wrong":
        headers.append((name, wrong))
    elif variant == "duplicate":
        value = dict(HEADERS)[name]
        headers.extend([(name, value), (name.upper(), value)])
    response_status, response = post(provider, headers=headers, path=path)
    assert response_status == status
    assert response["error"]["code"] == "local_transport_rejected"
    assert provider.calls == []


@pytest.mark.parametrize(
    "content_type",
    [
        b"application/json;charset=latin-1",
        b"application/json; charset=utf-8; other=x",
        b"application/json; charset=utf-8; charset=utf-8",
        b"application/json; nonsense",
        b"application/json, text/plain",
    ],
    ids=lambda value: type(value).__name__,
)
def test_content_type_policy_is_not_broadened(content_type):
    provider = Provider()
    headers = [(n, content_type if n == b"content-type" else v) for n, v in HEADERS]
    assert post(provider, headers=headers)[0] == 415
    assert provider.calls == []


@pytest.mark.parametrize(
    "content_type",
    [
        b"application/json",
        b"APPLICATION/JSON; CHARSET=UTF-8",
    ],
    ids=lambda value: type(value).__name__,
)
def test_existing_json_policy_and_case_insensitive_header_names(content_type):
    provider = Provider()
    headers = [
        (n.upper(), content_type if n == b"content-type" else v) for n, v in HEADERS
    ]
    assert post(provider, headers=headers) == (
        200,
        {"state": "unsupported", "candidate": None},
    )
    assert provider.calls == ["Hola"]


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b"[]",
        b"null",
        b'{"text":3}',
        b'{"text":false}',
        b'{"text":[]}',
        b'{"text":null}',
        b'{"text":""}',
        b'{"text":" "}',
        b'{"text":"\\ud800"}',
        b'{"text":"Hola","text":"Hola"}',
        b'{"text":"Hola","te\\u0078t":"Hola"}',
        b'{"text":"Hola","eligible":true}',
        b'{"text":"Hola","reason":"safe_unrecognized"}',
        b'{"text":"Hola","proof":"x"}',
        b'{"text":"Hola","requested_workspace_id":"x"}',
        b'{"text":"Hola","actor":"x"}',
        b'{"text":"Hola","permissions":[]}',
        b'{"text":"Hola","allow_cognitive_fallback":true}',
        b'{"text":"Hola","model":"x"}',
        b'{"text":"Hola","url":"http://evil.test"}',
        b'{"text":"Hola"} {}',
        b"\xff",
        b'{"text":NaN}',
        b'{"text":Infinity}',
        json.dumps({"text": "x" * 8193}).encode(),
    ],
    ids=lambda value: type(value).__name__,
)
def test_exact_text_only_body_rejects_bypass_and_authority_fields(body):
    provider = Provider(error=AssertionError("no call"))
    assert post(provider, body=body) == (
        400,
        {"state": "unsupported", "candidate": None},
    )
    assert provider.calls == []


def test_request_body_bound_enforced_across_chunks():
    provider = Provider()
    assert post(provider, chunks=[b"x" * 50000, b"x" * 50000]) == (
        400,
        {"state": "unsupported", "candidate": None},
    )
    assert provider.calls == []


def test_original_code_point_budget_accepts_escaped_supplementary_characters():
    text = "😀" * 8192
    provider = Provider()
    assert post(provider, text)[0] == 200
    assert provider.calls == [text]


@pytest.mark.parametrize(
    "provider,expected",
    [
        (
            Provider(error=PreparationProviderUnavailable("secret model")),
            "provider_unavailable",
        ),
        (Provider(error=RuntimeError("secret prompt")), "provider_failure"),
        (Provider("not JSON"), "provider_failure"),
        (Provider(), "unsupported"),
    ],
    ids=lambda value: type(value).__name__,
)
def test_sanitized_closed_failures_have_null_candidate(provider, expected):
    assert post(provider) == (200, {"state": expected, "candidate": None})
    assert provider.calls == ["Hola"]


def test_default_unconfigured_composition_is_inert_and_unavailable():
    app = create_local_interactive_app(Runtime())
    assert asyncio.run(request(app)) == (
        200,
        {"state": "provider_unavailable", "candidate": None},
    )


def test_composition_uses_only_explicit_configuration_and_never_generic_defaults(
    monkeypatch,
):
    import app.api.interactive as composition

    constructed = []
    provider = Provider()

    def factory(url, model):
        constructed.append((url, model))
        return provider

    monkeypatch.setattr(composition, "OllamaIntentPreparationProvider", factory)
    app = composition.create_local_interactive_app(
        Runtime(),
        intent_preparation_url="http://127.0.0.1:11434/api/generate",
        intent_preparation_model="explicit:test",
    )
    assert constructed == [("http://127.0.0.1:11434/api/generate", "explicit:test")]
    assert asyncio.run(request(app))[0] == 200
    assert provider.calls == ["Hola"]


def test_route_exists_only_in_local_interactive_surface():
    from app.main import app as public_app

    local = create_local_interactive_app(
        Runtime(), intent_preparation_provider=Provider()
    )
    assert PATH in local.openapi()["paths"]
    assert PATH not in public_app.openapi()["paths"]
    assert asyncio.run(request(local, method="GET"))[0] == 405


def test_preparation_never_calls_gateway_or_storage(monkeypatch):
    from app.infrastructure.local_storage.sqlite_storage import SQLiteLocalStorage
    from app.local_command import LocalCommandApplicationGateway

    def forbidden(*args, **kwargs):
        pytest.fail("preparation crossed authority/storage boundary")

    monkeypatch.setattr(LocalCommandApplicationGateway, "execute", forbidden)
    monkeypatch.setattr(SQLiteLocalStorage, "open", forbidden)
    monkeypatch.setattr(SQLiteLocalStorage, "initialize", forbidden)
    text = "Conserva literalmente knowledge find :: tema"
    fields = {"value": "knowledge find :: tema"}
    provider = Provider(
        json.dumps(
            {"outcome": "supported", "intent": "CAPTURE_KNOWLEDGE", "fields": fields}
        )
    )
    assert post(provider, text) == (
        200,
        {
            "state": "candidate_accepted",
            "candidate": {
                "intent": "CAPTURE_KNOWLEDGE",
                "fields": fields,
                "provenance": "local_model_assisted",
            },
        },
    )
    assert provider.calls == [text]
