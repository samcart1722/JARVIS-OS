"""Behavioral tests for the public cognitive endpoint."""

import asyncio
import json
from unittest.mock import Mock
from urllib.parse import urlencode

from fastapi import FastAPI

from app.api.routes import brain
from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.engine import CognitiveEngine
from app.core.container import Container

app = FastAPI()
app.include_router(brain.router)


def post_think(prompt: str) -> tuple[int, dict[str, str] | str]:
    """Call the real ASGI application without an external HTTP client."""
    messages = []
    request_sent = False

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/brain/think",
        "raw_path": b"/brain/think",
        "query_string": urlencode({"prompt": prompt}).encode(),
        "root_path": "",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    try:
        asyncio.run(app(scope, receive, send))
    except RuntimeError:
        if not messages:
            raise

    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = body.decode()
    return response_start["status"], payload


def test_think_uses_the_container_engine_and_preserves_http_contract(
    monkeypatch,
) -> None:
    engine = Mock(spec=CognitiveEngine)
    engine.process.return_value = "Response produced by ResponseStage."
    monkeypatch.setattr(brain.container, "cognitive_engine", engine)

    status, payload = post_think("Prepare a monthly order")

    assert status == 200
    assert payload == {
        "input": "Prepare a monthly order",
        "response": "Response produced by ResponseStage.",
    }
    engine.process.assert_called_once_with("Prepare a monthly order")


def test_think_does_not_hide_cognitive_engine_errors(monkeypatch) -> None:
    engine = Mock(spec=CognitiveEngine)
    engine.process.side_effect = RuntimeError("cognitive runtime failed")
    monkeypatch.setattr(brain.container, "cognitive_engine", engine)

    status, payload = post_think("Prepare a monthly order")

    assert status == 500
    assert payload == "Internal Server Error"


def test_container_composes_the_cognitive_engine() -> None:
    composed = Container()

    assert isinstance(composed.cognitive_engine, CognitiveEngine)


def test_think_returns_output_from_the_real_deterministic_capability() -> None:
    status, payload = post_think("Return this deterministic input")

    assert status == 200
    assert payload == {
        "input": "Return this deterministic input",
        "response": "Return this deterministic input",
    }


def test_controlled_capability_failure_is_not_presented_as_success(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        brain.container.normalized_input_capability,
        "execute",
        lambda context, step: CapabilityResult(
            success=False,
            errors=("controlled internal failure",),
        ),
    )

    status, payload = post_think("Trigger a controlled failure")

    assert status == 200
    assert payload == {
        "input": "Trigger a controlled failure",
        "response": "Plan execution failed.",
    }
