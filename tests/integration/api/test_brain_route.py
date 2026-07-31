"""Behavioral tests for the public cognitive endpoint."""

import asyncio
import json
from unittest.mock import Mock
from urllib.parse import urlencode

from fastapi import FastAPI

from app.api.routes import brain
from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CAPABILITY_NOT_FOUND,
    CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.engine import CognitiveEngine
from app.core.container import Container

app = FastAPI()
app.include_router(brain.router)


def post_think(prompt: str) -> tuple[int, dict[str, object] | str]:
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
    engine.process.return_value = CognitiveOutcome(
        success=True,
        response="Response produced by ResponseStage.",
    )
    monkeypatch.setattr(brain.container, "cognitive_engine", engine)

    status, payload = post_think("Prepare a monthly order")

    assert status == 200
    assert payload == {
        "success": True,
        "prompt": "Prepare a monthly order",
        "input": "Prepare a monthly order",
        "response": "Response produced by ResponseStage.",
        "error": None,
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
        "success": True,
        "prompt": "Return this deterministic input",
        "input": "Return this deterministic input",
        "response": "Return this deterministic input",
        "error": None,
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

    assert status == 503
    assert payload == {
        "success": False,
        "prompt": "Trigger a controlled failure",
        "input": "Trigger a controlled failure",
        "response": None,
        "error": {
            "code": CAPABILITY_EXECUTION_FAILED,
            "message": ("The requested cognitive capability could not complete."),
        },
    }
    serialized = json.dumps(payload)
    assert "controlled internal failure" not in serialized
    assert "Traceback" not in serialized
    assert "C:\\" not in serialized


def test_default_public_path_does_not_invoke_reasoning_provider(
    monkeypatch,
) -> None:
    generate = Mock(side_effect=AssertionError("reasoning must stay disabled"))
    monkeypatch.setattr(brain.container.reasoning_provider, "generate", generate)

    status, payload = post_think("Analyze this prompt")

    assert status == 200
    assert payload == {
        "success": True,
        "prompt": "Analyze this prompt",
        "input": "Analyze this prompt",
        "response": "Analyze this prompt",
        "error": None,
    }
    generate.assert_not_called()


def test_missing_capability_maps_to_safe_http_500(monkeypatch) -> None:
    engine = Mock(spec=CognitiveEngine)
    engine.process.return_value = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_NOT_FOUND),
    )
    monkeypatch.setattr(brain.container, "cognitive_engine", engine)

    status, payload = post_think("Request unavailable capability")

    assert status == 500
    assert payload == {
        "success": False,
        "prompt": "Request unavailable capability",
        "input": "Request unavailable capability",
        "response": None,
        "error": {
            "code": CAPABILITY_NOT_FOUND,
            "message": "The requested cognitive capability is unavailable.",
        },
    }


def test_unexpected_error_does_not_expose_internal_details(monkeypatch) -> None:
    engine = Mock(spec=CognitiveEngine)
    engine.process.side_effect = RuntimeError(
        "provider http://internal C:\\secret\\model"
    )
    monkeypatch.setattr(brain.container, "cognitive_engine", engine)

    status, payload = post_think("Unexpected failure")

    assert status == 500
    assert payload == "Internal Server Error"


def test_verifier_protocol_failure_maps_to_safe_public_503(monkeypatch) -> None:
    engine = Mock(spec=CognitiveEngine)
    engine.process.return_value = CognitiveOutcome(
        success=False,
        error=cognitive_error(CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID),
    )
    monkeypatch.setattr(brain.container, "cognitive_engine", engine)

    status, payload = post_think("Trigger verifier failure")

    assert status == 503
    assert payload["response"] is None
    assert payload["error"] == {
        "code": CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
        "message": "The claim evidence verifier returned an invalid response.",
    }
    serialized = json.dumps(payload)
    assert "private verifier response" not in serialized
    assert "http://" not in serialized
