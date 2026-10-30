"""Block D: composed adapter, parser, validator and service failure proofs."""

import asyncio
import io
import json
from threading import BoundedSemaphore

import pytest
import requests

from app.cognition.intent_preparation.service import IntentPreparationService
from app.cognition.providers import ollama_intent_preparation as adapter

URL = "http://127.0.0.1:11434/api/generate"
TEXT = "Conserva café"
GOOD = json.dumps(
    {"outcome": "supported", "intent": "CAPTURE_KNOWLEDGE", "fields": {"value": "café"}}
)


def envelope(candidate=GOOD):
    return json.dumps({"done": True, "response": candidate}).encode()


class Raw:
    def __init__(self, body, clock, late=False):
        self.source = io.BytesIO(body)
        self.sizes, self.total, self.clock, self.late = [], 0, clock, late

    def read(self, size, *, decode_content):
        assert decode_content is False and 0 < size <= 4096
        self.sizes.append(size)
        data = self.source.read(size)
        self.total += len(data)
        if self.late:
            self.clock[0] = 31.0
        return data


class Reply:
    def __init__(self, body, status, headers, clock, late):
        self.raw = Raw(body, clock, late)
        self.status_code, self.headers, self.closed = status, headers, False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    @property
    def content(self):
        pytest.fail("Unbounded response buffering")

    def json(self):
        pytest.fail("Unbounded response JSON parsing")


class Session:
    def __init__(self, reply, error):
        self.reply, self.error = reply, error
        self.trust_env, self.calls, self.closed = True, [], False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def mount(self, prefix, transport):
        assert prefix == "http://" and transport.max_retries.total == 0

    def post(self, url, **options):
        self.calls.append((url, options))
        assert url == URL and self.trust_env is False
        assert options["proxies"] == {} and options["allow_redirects"] is False
        assert options["headers"] == {"Accept-Encoding": "identity"}
        assert options["stream"] is True
        assert set(options["json"]) == {
            "model",
            "system",
            "prompt",
            "stream",
            "format",
            "options",
        }
        assert options["json"]["model"] == "synthetic:D"
        assert (
            options["json"]["stream"] is False and options["json"]["format"] == "json"
        )
        assert options["timeout"][0] <= 3 and options["timeout"][1] < 30
        if self.error:
            raise self.error
        return self.reply


class Connection:
    def __init__(self, channel, clock, stalled):
        self.channel, self.clock, self.stalled = channel, clock, stalled

    def send_bytes(self, data):
        self.channel.append(data)

    def poll(self, timeout):
        assert 0 < timeout <= 29.5
        if self.stalled:
            self.clock[0] += timeout
        return bool(self.channel)

    def recv_bytes(self, maximum):
        assert maximum == 32771
        value = self.channel.pop()
        if len(value) > maximum:
            raise OSError("oversized message")
        return value

    def close(self):
        pass


class Context:
    def __init__(self, clock, stalled):
        self.clock, self.stalled, self.processes = clock, stalled, []

    def Pipe(self, *, duplex):
        assert duplex is False
        shared = []
        return (
            Connection(shared, self.clock, self.stalled),
            Connection(shared, self.clock, self.stalled),
        )

    def Process(self, *, target, args, daemon):
        assert target is adapter._worker and daemon is True
        owner = self

        class Process:
            alive = False
            terminated = False
            killed = False
            closed = False

            def start(self):
                self.alive = owner.stalled
                if not owner.stalled:
                    target(*args)

            def is_alive(self):
                return self.alive

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.killed = True
                self.alive = False

            def join(self, timeout):
                assert 0 <= timeout <= 0.5
                if owner.stalled:
                    owner.clock[0] += timeout

            def close(self):
                self.closed = True

        process = Process()
        self.processes.append(process)
        return process


def candidate(**overrides):
    return json.dumps(
        {
            "outcome": "supported",
            "intent": "CAPTURE_KNOWLEDGE",
            "fields": {"value": "café"},
            **overrides,
        }
    )


CASES = [
    (
        "connection-refused",
        None,
        requests.ConnectionError("SECRET_PROMPT"),
        200,
        TEXT,
        "provider_unavailable",
    ),
    (
        "timeout-exception",
        None,
        requests.Timeout("SECRET_PROMPT"),
        200,
        TEXT,
        "provider_failure",
    ),
    ("model-missing", None, None, 404, TEXT, "provider_unavailable"),
    ("http-error", None, None, 503, TEXT, "provider_failure"),
    ("redirect", None, None, 302, TEXT, "provider_failure"),
    (
        "transport-exception",
        None,
        RuntimeError("SECRET_PROMPT"),
        200,
        TEXT,
        "provider_failure",
    ),
    ("malformed-outer", b"SECRET_NOT_JSON", None, 200, TEXT, "provider_failure"),
    (
        "duplicate-outer",
        b'{"done":true,"done":true,"response":"{}"}',
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    ("malformed-candidate", envelope("{"), None, 200, TEXT, "provider_failure"),
    (
        "duplicate-candidate",
        envelope(
            '{"outcome":"unsupported","outcome":"supported","intent":null,"fields":{}}'
        ),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "extra-key",
        envelope(candidate(command="list read hidden")),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "unknown-intent",
        envelope(candidate(intent="UNKNOWN")),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "fifth-intent",
        envelope(candidate(intent="DELETE_KNOWLEDGE")),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "tool-payload",
        envelope(candidate(fields={"value": "café", "tool": "execute"})),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "unsupported",
        envelope('{"outcome":"unsupported","intent":null,"fields":{}}'),
        None,
        200,
        TEXT,
        "unsupported",
    ),
    ("prose", envelope("Here is JSON: " + GOOD), None, 200, TEXT, "provider_failure"),
    ("array", envelope("[" + GOOD + "]"), None, 200, TEXT, "provider_failure"),
    (
        "nested",
        envelope(candidate(fields={"value": {"nested": "café"}})),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "number",
        envelope(candidate(fields={"value": 42})),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "non-grounded",
        envelope(candidate(fields={"value": "invented"})),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    (
        "wrong-role",
        envelope(
            candidate(
                intent="ADD_FOLLOW_UP", fields={"item": "Compras", "list_id": "Compras"}
            )
        ),
        None,
        200,
        "Incorpora pan a la lista Compras",
        "provider_failure",
    ),
    (
        "ambiguous",
        envelope(candidate(intent="READ_FOLLOW_UP", fields={"list_id": "Compras"})),
        None,
        200,
        "¿la lista Compras y la lista Hogar?",
        "unsupported",
    ),
    (
        "oversized-field",
        envelope(candidate(fields={"value": "x" * 8193})),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    ("oversized-body", b" " * 100000, None, 200, TEXT, "provider_failure"),
    (
        "surrogate",
        envelope(candidate(fields={"value": "\ud800"})),
        None,
        200,
        TEXT,
        "provider_failure",
    ),
    ("valid-semantic-only", envelope(), None, 200, TEXT, "candidate_accepted"),
]


@pytest.mark.parametrize(
    "name,body,error,status,text,expected", CASES, ids=[c[0] for c in CASES]
)
def test_adapter_to_service_failure_matrix(
    monkeypatch, name, body, error, status, text, expected
):
    clock = [0.0]
    monkeypatch.setattr(adapter, "monotonic", lambda: clock[0])
    monkeypatch.setattr(adapter, "_SLOT", BoundedSemaphore(1))
    reply = Reply(body if body is not None else envelope(), status, {}, clock, False)
    session = Session(reply, error)
    monkeypatch.setattr(adapter.requests, "Session", lambda: session)
    context = Context(clock, False)

    def get_context(method):
        assert method == "spawn"
        return context

    monkeypatch.setattr(adapter.multiprocessing, "get_context", get_context)
    provider = adapter.OllamaIntentPreparationProvider(URL, "synthetic:D")
    wire = asyncio.run(IntentPreparationService(provider).prepare(text)).to_wire()
    assert set(wire) == {"state", "candidate"} and wire["state"] == expected
    if expected != "candidate_accepted":
        assert wire["candidate"] is None
    else:
        assert wire["candidate"] == {
            "intent": "CAPTURE_KNOWLEDGE",
            "fields": {"value": "café"},
            "provenance": "local_model_assisted",
        }
        assert "command" not in wire["candidate"]
    assert len(session.calls) == (0 if name == "ambiguous" else 1)
    assert reply.raw.total <= 32769
    assert "SECRET_PROMPT" not in json.dumps(wire)
    assert all(p.closed for p in context.processes)
    assert adapter._SLOT.acquire(blocking=False)
    adapter._SLOT.release()


@pytest.mark.parametrize(
    "url,model",
    [
        (None, None),
        (URL, None),
        ("https://127.0.0.1:11434/api/generate", "synthetic:D"),
        ("http://example.com:11434/api/generate", "synthetic:D"),
        (URL + "?model=caller", "synthetic:D"),
        (URL, "bad model"),
    ],
)
def test_invalid_configuration_never_opens_transport(monkeypatch, url, model):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid configuration performed provider I/O")

    monkeypatch.setattr(adapter.requests, "Session", forbidden)
    monkeypatch.setattr(adapter.multiprocessing, "get_context", forbidden)
    provider = adapter.OllamaIntentPreparationProvider(url, model)
    assert asyncio.run(IntentPreparationService(provider).prepare(TEXT)).to_wire() == {
        "state": "provider_unavailable",
        "candidate": None,
    }


@pytest.mark.parametrize("mode", ["stalled-worker", "late-body", "oversized-length"])
def test_composed_deadline_size_and_cleanup(monkeypatch, mode):
    clock = [0.0]
    monkeypatch.setattr(adapter, "monotonic", lambda: clock[0])
    monkeypatch.setattr(adapter, "_SLOT", BoundedSemaphore(1))
    reply = Reply(
        envelope(),
        200,
        {"Content-Length": "32769"} if mode == "oversized-length" else {},
        clock,
        mode == "late-body",
    )
    session = Session(reply, None)
    monkeypatch.setattr(adapter.requests, "Session", lambda: session)
    context = Context(clock, mode == "stalled-worker")
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda method: context)
    result = asyncio.run(
        IntentPreparationService(
            adapter.OllamaIntentPreparationProvider(URL, "synthetic:D")
        ).prepare(TEXT)
    ).to_wire()
    assert result == {"state": "provider_failure", "candidate": None}
    assert len(context.processes) == 1 and context.processes[0].closed
    if mode == "stalled-worker":
        assert clock[0] <= 30
        assert context.processes[0].terminated and context.processes[0].killed
        assert session.calls == []
    if mode == "oversized-length":
        assert reply.raw.total == 0
    assert adapter._SLOT.acquire(blocking=False)
    adapter._SLOT.release()


def test_cancelled_admitted_service_retains_capacity_until_real_thread_finishes(
    monkeypatch,
):
    from threading import Event

    from app.cognition.intent_preparation import service as module

    entered, release = Event(), Event()
    calls, tasks = [], []

    class Blocking:
        def prepare(self, text):
            calls.append(text)
            entered.set()
            assert release.wait(3), "bounded synthetic worker release"
            return GOOD

    async def exercise():
        service = IntentPreparationService(Blocking())
        real_wait = asyncio.wait

        async def observe(awaitables, timeout):
            tasks.extend(awaitables)
            assert 0 <= timeout <= 30
            return await real_wait(awaitables, timeout=timeout)

        monkeypatch.setattr(module.asyncio, "wait", observe)
        first = asyncio.create_task(service.prepare(TEXT))
        try:
            assert await asyncio.to_thread(entered.wait, 2)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert (await service.prepare(TEXT)).to_wire() == {
                "state": "provider_failure",
                "candidate": None,
            }
            assert calls == [TEXT] and len(tasks) == 1
            release.set()
            await asyncio.wait_for(tasks[0], timeout=2)
            await asyncio.sleep(0)  # completion callback, not a wall-clock sleep
            assert (await service.prepare(TEXT)).state.value == "candidate_accepted"
            assert calls == [TEXT, TEXT]
        finally:
            release.set()
            if not first.done():
                first.cancel()
                await asyncio.gather(first, return_exceptions=True)

    asyncio.run(exercise())
