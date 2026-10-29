"""HTTP/process doubles only: no live provider requests or generations."""

import io
import json

import pytest
import requests

from app.cognition.intent_preparation.contracts import (
    PreparationProviderFailure,
    PreparationProviderUnavailable,
)
from app.cognition.providers import ollama_intent_preparation as adapter

URL = "http://127.0.0.1:11434/api/generate"
CANDIDATE = '{"outcome":"unsupported","intent":null,"fields":{}}'


class Raw:
    def __init__(self, body):
        self.source = io.BytesIO(body)
        self.sizes = []
        self.read_bytes = 0

    def read(self, size, *, decode_content):
        assert decode_content is False
        self.sizes.append(size)
        data = self.source.read(size)
        self.read_bytes += len(data)
        return data


class Response:
    def __init__(self, body=b"", status=200, headers=None):
        self.status_code = status
        self.headers = headers or {}
        self.raw = Raw(body)
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    @property
    def content(self):
        pytest.fail("unbounded buffering is forbidden")

    def json(self):
        pytest.fail("unbounded JSON buffering is forbidden")


class Session:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []
        self.mounts = []
        self.trust_env = True
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def mount(self, prefix, transport):
        self.mounts.append((prefix, transport.max_retries.total))

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.response


def envelope(candidate=CANDIDATE, **extra):
    return json.dumps({"done": True, "response": candidate, **extra}).encode()


def install(monkeypatch, response=None, error=None):
    session = Session(response, error)
    monkeypatch.setattr(adapter.requests, "Session", lambda: session)
    return session


def test_one_exchange_has_no_proxies_redirects_or_model_streaming(monkeypatch):
    response = Response(envelope())
    session = install(monkeypatch, response)
    assert (
        adapter._generate(URL, "explicit:test", "Hola") == b"ok:" + CANDIDATE.encode()
    )
    assert session.trust_env is False
    assert session.mounts == [("http://", 0)]
    assert len(session.calls) == 1
    args, options = session.calls[0]
    assert args == (URL,)
    assert options["proxies"] == {}
    assert options["allow_redirects"] is False
    assert options["stream"] is True
    assert options["headers"] == {"Accept-Encoding": "identity"}
    assert options["json"]["stream"] is False
    assert options["json"]["model"] == "explicit:test"
    assert options["json"]["prompt"] == "Hola"
    assert options["timeout"][0] <= 3 and options["timeout"][1] < 30
    assert response.closed and session.closed


@pytest.mark.parametrize(
    "url,model",
    [
        (None, None),
        (URL, None),
        (None, "explicit"),
        (URL, ""),
        (URL, " space "),
        ("https://127.0.0.1:11434/api/generate", "explicit"),
        ("http://localhost:11434/api/generate", "explicit"),
        ("http://example.com:11434/api/generate", "explicit"),
        ("http://192.168.1.1:11434/api/generate", "explicit"),
        ("http://169.254.169.254:80/api/generate", "explicit"),
        ("http://user:pass@127.0.0.1:11434/api/generate", "explicit"),
        (URL + "?url=remote", "explicit"),
        (URL + "#fragment", "explicit"),
        ("http://127.0.0.1/api/generate", "explicit"),
        ("http://127.0.0.1:0/api/generate", "explicit"),
        ("http://127.0.0.1:65536/api/generate", "explicit"),
        ("http://127.0.0.1:11434/api/tags", "explicit"),
        ("http://127.0.0.1:11434/api/generate\n", "explicit"),
        ("http://[::ffff:192.168.1.1]:11434/api/generate", "explicit"),
    ],
    ids=lambda value: type(value).__name__,
)
def test_invalid_configuration_is_unavailable_before_any_io(monkeypatch, url, model):
    def forbidden(*args, **kwargs):
        pytest.fail("configuration rejection must precede I/O")

    monkeypatch.setattr(adapter.multiprocessing, "get_context", forbidden)
    monkeypatch.setattr(adapter.requests, "Session", forbidden)
    provider = adapter.OllamaIntentPreparationProvider(url, model)
    with pytest.raises(PreparationProviderUnavailable):
        provider.prepare("Hola")


@pytest.mark.parametrize(
    "url",
    [
        URL,
        "http://[::1]:11434/api/generate",
        "http://127.0.0.2:11434/api/generate",
    ],
    ids=lambda value: type(value).__name__,
)
def test_only_explicit_numeric_loopback_targets_are_configurable(url):
    assert adapter._configuration(url, "explicit:test") == (url, "explicit:test")


@pytest.mark.parametrize(
    "text",
    [None, "", " ", "x" * 8193, "\ud800"],
    ids=lambda value: type(value).__name__,
)
def test_invalid_provider_input_never_creates_a_worker(monkeypatch, text):
    monkeypatch.setattr(
        adapter.multiprocessing, "get_context", lambda *args: pytest.fail("no worker")
    )
    with pytest.raises(PreparationProviderFailure):
        adapter.OllamaIntentPreparationProvider(URL, "explicit").prepare(text)


@pytest.mark.parametrize(
    "status,expected",
    [
        (301, b"failure"),
        (302, b"failure"),
        (307, b"failure"),
        (308, b"failure"),
        (400, b"failure"),
        (404, b"unavailable"),
        (500, b"failure"),
    ],
    ids=lambda value: type(value).__name__,
)
def test_status_failures_never_redirect_or_retry(monkeypatch, status, expected):
    response = Response(b"secret", status)
    session = install(monkeypatch, response)
    assert adapter._generate(URL, "explicit", "Hola") == expected
    assert len(session.calls) == 1
    assert response.raw.read_bytes == 0


@pytest.mark.parametrize(
    "headers,body",
    [
        ({"Content-Length": "32769"}, b""),
        ({"Content-Length": "-1"}, b""),
        ({"Content-Length": "not a number"}, b""),
        ({"Content-Encoding": "gzip"}, b"compressed"),
        ({}, b"x" * 100000),
        ({}, envelope(CANDIDATE, padding="x" * 32768)),
    ],
    ids=lambda value: type(value).__name__,
)
def test_full_transport_envelope_bound_before_buffering(monkeypatch, headers, body):
    response = Response(body, headers=headers)
    install(monkeypatch, response)
    assert adapter._generate(URL, "explicit", "Hola") == b"failure"
    assert response.raw.read_bytes <= 32769
    assert all(size <= 4096 for size in response.raw.sizes)


def test_exact_32768_byte_envelope_is_accepted(monkeypatch):
    base = envelope()
    body = base[:-1] + b" " * (32768 - len(base)) + b"}"
    assert len(body) == 32768
    response = Response(body)
    install(monkeypatch, response)
    assert adapter._generate(URL, "explicit", "Hola") == b"ok:" + CANDIDATE.encode()
    assert response.raw.read_bytes == 32768


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b"[]",
        b"prose",
        b'{"done":true,"response":"x","extra":NaN}',
        b'{"done":true,"response":"x","extra":Infinity}',
        b"{}{}",
        b"\xff",
        b'{"done":false,"response":"x"}',
        b'{"done":true,"response":3}',
        b'{"done":true,"done":true,"response":"x"}',
        b'{"done":true,"response":"x","response":"x"}',
        b'{"done":true,"response":"\\ud800"}',
    ],
    ids=lambda value: type(value).__name__,
)
def test_untrusted_transport_envelopes_fail_closed(monkeypatch, body):
    install(monkeypatch, Response(body))
    connection = Connection()
    adapter._worker(connection, URL, "explicit", "Hola")
    assert connection.sent == b"failure"
    assert connection.closed


@pytest.mark.parametrize(
    "error,expected",
    [
        (requests.ConnectionError("secret"), b"unavailable"),
        (requests.ReadTimeout("secret"), b"failure"),
        (requests.HTTPError("secret"), b"failure"),
        (RuntimeError("secret prompt"), b"failure"),
    ],
    ids=lambda value: type(value).__name__,
)
def test_worker_contains_exceptions_and_never_retries(monkeypatch, error, expected):
    session = install(monkeypatch, error=error)
    connection = Connection()
    adapter._worker(connection, URL, "explicit", "Hola")
    assert connection.sent == expected
    assert connection.closed and len(session.calls) == 1


def test_drip_feed_hits_wall_clock_guard_between_bounded_reads(monkeypatch):
    clock = iter([0, 0, 0, 1, 40])
    monkeypatch.setattr(adapter, "monotonic", lambda: next(clock))
    response = Response(b"x" * 10000)
    install(monkeypatch, response)
    assert adapter._generate(URL, "explicit", "Hola") == b"failure"
    assert response.raw.read_bytes == 4096


class Connection:
    def __init__(self, data=b"ok:" + CANDIDATE.encode(), ready=True):
        self.data, self.ready = data, ready
        self.closed = False
        self.sent = None
        self.waits = []

    def send_bytes(self, data):
        self.sent = data

    def poll(self, timeout):
        self.waits.append(timeout)
        return self.ready

    def recv_bytes(self, maxlength):
        assert maxlength == 32771
        return self.data

    def close(self):
        self.closed = True


class Process:
    def __init__(self, stubborn=False):
        self.alive = False
        self.stubborn = stubborn
        self.calls = []

    def start(self):
        self.alive = True
        self.calls.append("start")

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.calls.append("terminate")
        if not self.stubborn:
            self.alive = False

    def kill(self):
        self.calls.append("kill")
        self.alive = False

    def join(self, timeout):
        assert 0 <= timeout <= 30
        self.calls.append("join")

    def close(self):
        self.calls.append("close")


class Context:
    def __init__(self, connection, process):
        self.receiver, self.sender = connection, Connection()
        self.process = process
        self.created = []

    def Pipe(self, duplex):
        assert duplex is False
        return self.receiver, self.sender

    def Process(self, **kwargs):
        self.created.append(kwargs)
        assert kwargs["target"] is adapter._worker
        assert kwargs["daemon"] is True
        return self.process


@pytest.mark.parametrize(
    "data,error",
    [
        (b"ok:" + CANDIDATE.encode(), None),
        (b"unavailable", PreparationProviderUnavailable),
        (b"failure", PreparationProviderFailure),
        (b"ok:\xff", PreparationProviderFailure),
    ],
    ids=lambda value: type(value).__name__,
)
def test_parent_accepts_only_bounded_worker_messages_and_cleans_up(
    monkeypatch, data, error
):
    connection, process = Connection(data), Process()
    context = Context(connection, process)
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda mode: context)
    provider = adapter.OllamaIntentPreparationProvider(URL, "explicit")
    if error:
        with pytest.raises(error, match="Local provider"):
            provider.prepare("Hola")
    else:
        assert provider.prepare("Hola") == CANDIDATE
    assert len(context.created) == 1
    assert context.created[0]["args"] == (context.sender, URL, "explicit", "Hola")
    assert process.calls == ["start", "terminate", "join", "close"]
    assert connection.closed and context.sender.closed
    assert 0 < connection.waits[0] <= 29.5


def test_parent_deadline_terminates_and_kills_stalled_worker_without_retry(monkeypatch):
    context = Context(Connection(ready=False), Process(stubborn=True))
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda mode: context)
    with pytest.raises(PreparationProviderFailure):
        adapter.OllamaIntentPreparationProvider(URL, "explicit").prepare("Hola")
    assert context.process.calls == [
        "start",
        "terminate",
        "join",
        "kill",
        "join",
        "close",
    ]
    assert len(context.created) == 1


def test_global_provider_admission_rejects_concurrent_work_before_worker_creation(
    monkeypatch,
):
    monkeypatch.setattr(
        adapter.multiprocessing,
        "get_context",
        lambda *args: pytest.fail("must not queue"),
    )
    assert adapter._SLOT.acquire(blocking=False)
    try:
        with pytest.raises(PreparationProviderFailure, match="busy"):
            adapter.OllamaIntentPreparationProvider(URL, "explicit").prepare("Hola")
    finally:
        adapter._SLOT.release()


def test_worker_emits_only_bounded_success_bytes(monkeypatch):
    install(monkeypatch, Response(envelope()))
    connection = Connection()
    adapter._worker(connection, URL, "explicit", "Hola")
    assert connection.sent == b"ok:" + CANDIDATE.encode()
    assert connection.closed


def test_parent_contains_start_failure_and_releases_admission(monkeypatch):
    context = Context(Connection(), Process())

    def fail_start():
        raise OSError("secret OS details")

    context.process.start = fail_start
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda mode: context)
    with pytest.raises(PreparationProviderFailure, match="Local provider failed"):
        adapter.OllamaIntentPreparationProvider(URL, "explicit").prepare("Hola")
    assert context.receiver.closed and context.sender.closed
    assert adapter._SLOT.acquire(blocking=False)
    adapter._SLOT.release()


def test_parent_contains_broken_pipe_and_releases_admission(monkeypatch):
    context = Context(Connection(), Process())

    def broken(maxlength):
        raise EOFError("secret")

    context.receiver.recv_bytes = broken
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda mode: context)
    with pytest.raises(PreparationProviderFailure):
        adapter.OllamaIntentPreparationProvider(URL, "explicit").prepare("Hola")
    assert context.process.calls == ["start", "terminate", "join", "close"]
    assert context.receiver.closed and context.sender.closed


def test_parent_rejects_message_arriving_after_total_budget(monkeypatch):
    context = Context(Connection(), Process())
    clock = iter([0, 0, 30, 30])
    monkeypatch.setattr(adapter, "monotonic", lambda: next(clock))
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda mode: context)
    with pytest.raises(PreparationProviderFailure):
        adapter.OllamaIntentPreparationProvider(URL, "explicit").prepare("Hola")
    assert context.process.calls == ["start", "terminate", "join", "close"]


def test_failed_os_cleanup_cannot_admit_another_worker(monkeypatch):
    from threading import BoundedSemaphore

    slot = BoundedSemaphore(1)
    monkeypatch.setattr(adapter, "_SLOT", slot)
    context = Context(Connection(ready=False), Process(stubborn=True))
    context.process.kill = lambda: context.process.calls.append("kill")
    monkeypatch.setattr(adapter.multiprocessing, "get_context", lambda mode: context)
    provider = adapter.OllamaIntentPreparationProvider(URL, "explicit")
    with pytest.raises(PreparationProviderFailure):
        provider.prepare("Hola")
    assert context.process.alive
    with pytest.raises(PreparationProviderFailure, match="busy"):
        provider.prepare("Hola")
    assert len(context.created) == 1
