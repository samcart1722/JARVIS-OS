"""Block D: endpoint -> production UI -> real interpreter -> governed synthetic Send."""

import asyncio
import hashlib
import json
import subprocess

import pytest
import requests

from app.api.interactive import create_local_interactive_app
from app.cognition.engine import CognitiveEngine
from app.cognition.interpretation.interpreter import (
    DeterministicLocalCommandInterpreter,
)
from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    FindKnowledgeRecordsQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    RepositoryPermissionPolicy,
)
from app.infrastructure.local_storage.sqlite_storage import SQLiteLocalStorage
from app.local_command import LocalCommandApplicationGateway
from app.membership.service import MembershipDecisionService
from app.models.ollama_client import OllamaClient
from app.models.ollama_readiness_probe import OllamaReadinessProbe
from app.operations.local_interactive_runtime import (
    DEVELOPMENT_ACTOR,
    DEVELOPMENT_WORKSPACE,
    LocalInteractiveRuntime,
)
from app.principal_authentication import LocalAuthenticationProof, PrincipalIdentity

PROOF = "synthetic-block-D-proof"
META = {
    "record_id": "block-D-record",
    "kind": "fact",
    "key": "explicit-key",
    "source_type": "synthetic",
    "source_reference": "D:explicit",
}
VALUE = 'literal {"proof":"inert"}</script> e\u0301 😀 :: data'
KEY = 'Tema "Ágil" \\ ruta e\u0301 😀'
ITEM = 'pan "rojo" :: \\ruta\nsegunda línea 😀'
CASES = [
    (
        "CAPTURE_KNOWLEDGE",
        "Conserva " + VALUE,
        {"value": VALUE},
        META,
        StoreKnowledgeRecordCommand,
        KNOWLEDGE_RECORDS_ADD,
    ),
    (
        "RECALL_KNOWLEDGE",
        "Busca " + KEY,
        {"key": KEY},
        {"kind": "concept"},
        FindKnowledgeRecordsQuery,
        KNOWLEDGE_RECORDS_READ,
    ),
    (
        "ADD_FOLLOW_UP",
        "Incorpora " + ITEM + " a la lista ComprasD",
        {"item": ITEM, "list_id": "ComprasD"},
        {},
        AddListItemsCommand,
        LIST_ITEMS_ADD,
    ),
    (
        "READ_FOLLOW_UP",
        "¿Consulta la lista ComprasD?",
        {"list_id": "ComprasD"},
        {},
        ReadListItemsQuery,
        LIST_ITEMS_READ,
    ),
]


class Provider:
    def __init__(self):
        self.output, self.calls = "", []

    def prepare(self, text):
        self.calls.append(text)
        return self.output


async def post(app, token, path, payload):
    pending = [json.dumps(payload, ensure_ascii=True).encode()]
    events = []

    async def receive():
        return (
            {"type": "http.request", "body": pending.pop(), "more_body": False}
            if pending
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
            "client": ("synthetic", 1),
            "server": ("127.0.0.1", 8765),
            "headers": [
                (b"host", b"127.0.0.1:8765"),
                (b"origin", b"http://127.0.0.1:8765"),
                (b"content-type", b"application/json"),
                (b"x-luxiom-csrf", token.encode()),
            ],
        },
        receive,
        send,
    )
    status = next(e["status"] for e in events if e["type"] == "http.response.start")
    body = b"".join(
        e.get("body", b"") for e in events if e["type"] == "http.response.body"
    )
    return status, json.loads(body)


def ui(rows):
    result = subprocess.run(
        [
            "node",
            "--unhandled-rejections=strict",
            "tests/browser/local_model_intent_preparation_security.js",
            "--commands",
        ],
        input=json.dumps(rows, ensure_ascii=True),
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=30,
        check=True,
    )
    evidence = json.loads(result.stdout)
    assert evidence["forbiddenAccesses"] == evidence["realProviderCalls"] == 0
    assert evidence["nativeBrowserVerified"] is False
    assert evidence["checks"] > 100
    return evidence["commands"]


@pytest.fixture
def prepared_runtime(tmp_path, monkeypatch):
    counters = {
        k: 0
        for k in (
            "network",
            "cognitive",
            "storage",
            "memory",
            "gateway",
            "identity",
            "membership",
            "permission",
        )
    }

    def guard(name):
        def fail(*args, **kwargs):
            counters[name] += 1
            pytest.fail("Forbidden pre-Send dependency: " + name)

        return fail

    monkeypatch.setattr(requests.sessions.Session, "request", guard("network"))
    monkeypatch.setattr(OllamaClient, "chat", guard("network"))
    monkeypatch.setattr(OllamaReadinessProbe, "check", guard("network"))
    monkeypatch.setattr(CognitiveEngine, "process", guard("cognitive"))
    runtime = LocalInteractiveRuntime(tmp_path / "block-D.sqlite3", PROOF)
    runtime.start()  # Bootstrap/storage is explicitly outside the preparation proof.
    try:
        provider = Provider()
        app = create_local_interactive_app(
            runtime, intent_preparation_provider=provider
        )
        app.state.local_command_application_gateway = runtime.gateway
        token = runtime.csrf_token
        before_bytes = hashlib.sha256(runtime.database_path.read_bytes()).hexdigest()
        before_changes = runtime._storage._connection.total_changes
        rows = []
        with monkeypatch.context() as gates:
            gates.setattr(LocalCommandApplicationGateway, "execute", guard("gateway"))
            for method in (
                "_require_connection",
                "_require_initialized_connection",
                "open",
                "initialize",
            ):
                gates.setattr(SQLiteLocalStorage, method, guard("storage"))
            gates.setattr(MembershipDecisionService, "decide", guard("membership"))
            gates.setattr(RepositoryPermissionPolicy, "is_allowed", guard("permission"))
            for identity in (
                LocalAuthenticationProof,
                PrincipalIdentity,
                ActorIdentity,
                WorkspaceIdentity,
            ):
                gates.setattr(identity, "__init__", guard("identity"))
            for name in (
                "memory",
                "memory_pipeline",
                "scoped_memory_repository",
                "memory_context_retriever",
                "explicit_memory_update_service",
            ):
                port = getattr(runtime._container, name)
                for method in dir(type(port)):
                    if not method.startswith("_") and callable(
                        getattr(type(port), method)
                    ):
                        gates.setattr(type(port), method, guard("memory"))
            for family, text, fields, explicit, _, _ in CASES:
                provider.output = json.dumps(
                    {"outcome": "supported", "intent": family, "fields": fields}
                )
                status, wire = asyncio.run(
                    post(app, token, "/local/intent-preparation", {"text": text})
                )
                assert status == 200 and wire["state"] == "candidate_accepted"
                assert set(wire["candidate"]) == {"intent", "fields", "provenance"}
                rows.append({"text": text, "explicit": explicit, "envelope": wire})
            commands = ui(rows)
            assert counters == {k: 0 for k in counters}
            assert len(provider.calls) == 4
        assert runtime._storage._connection.total_changes == before_changes
        assert (
            hashlib.sha256(runtime.database_path.read_bytes()).hexdigest()
            == before_bytes
        )
        interpreter = DeterministicLocalCommandInterpreter()
        for row, (_, _, fields, explicit, kind, _) in zip(commands, CASES, strict=True):
            assert row["result"]["outcome"] == "prepared"
            assert len(row["text"]) <= 8192
            result = interpreter.interpret(row["text"], DEVELOPMENT_WORKSPACE)
            assert result.status.value == "interpreted" and type(result.intent) is kind
            intent = result.intent
            if kind is StoreKnowledgeRecordCommand:
                assert intent.record.value == fields["value"]
                assert intent.record.record_id == explicit["record_id"]
                assert intent.record.key == explicit["key"]
                assert intent.record.provenance.source_type == explicit["source_type"]
                assert (
                    intent.record.provenance.source_reference
                    == explicit["source_reference"]
                )
            elif kind is FindKnowledgeRecordsQuery:
                assert (
                    intent.key == fields["key"]
                    and intent.kind.value == explicit["kind"]
                )
            else:
                assert intent.list_id == fields["list_id"]
                if kind is AddListItemsCommand:
                    assert intent.items == (fields["item"],)
        yield runtime, app, token, commands, counters
        assert counters["network"] == counters["cognitive"] == 0
    finally:
        runtime.close()


@pytest.mark.parametrize("index", range(4), ids=[c[0] for c in CASES])
@pytest.mark.parametrize(
    "terminal",
    [
        "allowed",
        "bad-proof",
        "other-workspace",
        "inactive-membership",
        "revoked-permission",
        "extra-provenance",
    ],
)
def test_model_proposal_has_no_authority_over_governed_send(
    prepared_runtime, index, terminal
):
    runtime, app, token, commands, counters = prepared_runtime
    # All commands are prepared first. Only then alter current authority state.
    if terminal == "inactive-membership":
        runtime._storage.deactivate(DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE)
    if terminal == "revoked-permission":
        runtime._storage.revoke_permission_grant(
            DEVELOPMENT_ACTOR, DEVELOPMENT_WORKSPACE, CASES[index][5]
        )
    payload = {
        "proof": "wrong-proof" if terminal == "bad-proof" else PROOF,
        "requested_workspace_id": "other-workspace"
        if terminal == "other-workspace"
        else DEVELOPMENT_WORKSPACE.workspace_id,
        "text": commands[index]["text"],
        "allow_cognitive_fallback": False,
    }
    if terminal == "extra-provenance":
        payload["provenance"] = "local_model_assisted"
    before = runtime._storage._connection.total_changes
    status, wire = asyncio.run(post(app, token, "/local/command", payload))
    if terminal == "allowed":
        assert status == 200 and wire["success"] is True and wire["route"] == "local"
    else:
        expected = (
            "invalid_request"
            if terminal == "extra-provenance"
            else "local_permission_denied"
            if terminal == "revoked-permission"
            else "access_denied"
        )
        assert status == (400 if terminal == "extra-provenance" else 403)
        assert wire["success"] is False and wire["error"]["code"] == expected
        assert "projection" not in wire
        assert runtime._storage._connection.total_changes == before
    assert counters == {k: 0 for k in counters}


@pytest.mark.parametrize(
    "family,text,fields,explicit",
    [
        ("CAPTURE_KNOWLEDGE", "Conserva X", {"value": "X"}, {}),
        ("RECALL_KNOWLEDGE", "Busca K", {"key": "K"}, {"key": "conflict"}),
        (
            "READ_FOLLOW_UP",
            "Consulta la lista ComprasD",
            {"list_id": "ComprasD"},
            {"list_id": "Other"},
        ),
    ],
)
def test_partial_or_conflicting_fields_never_become_commands(
    family, text, fields, explicit
):
    from app.cognition.intent_preparation.service import IntentPreparationService

    p = Provider()
    p.output = json.dumps({"outcome": "supported", "intent": family, "fields": fields})
    wire = asyncio.run(IntentPreparationService(p).prepare(text)).to_wire()
    assert wire["state"] == "candidate_accepted"
    row = ui([{"text": text, "explicit": explicit, "envelope": wire}])[0]
    assert row["text"] == "" and row["result"]["outcome"] == "clarification_required"
    if family == "CAPTURE_KNOWLEDGE":
        assert set(row["result"]["missingFields"]) == set(META)
    else:
        assert row["result"]["conflictingFields"]
    assert p.calls == [text]
