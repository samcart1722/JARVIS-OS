import asyncio
import json
import platform
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI

from app.api.interactive import create_local_interactive_app
from app.cognition.interpretation.interpreter import (
    DeterministicLocalCommandInterpreter,
)
from app.cognition.local_resolution.models import AddListItemsCommand, WorkspaceIdentity
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
        message for message in messages if message["type"] == "http.response.start"
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
        self.elements_by_id: dict[str, dict[str, str | None]] = {}
        self.inline_styles = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = dict(attrs)
        if values.get("id") is not None:
            self.elements_by_id[cast(str, values["id"])] = values
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
    projection_ids = {
        "list-projection",
        "projection-list-id",
        "projection-added-row",
        "projection-added",
        "projection-already-present-row",
        "projection-already-present",
        "projection-items",
        "knowledge-projection",
        "knowledge-operation",
        "knowledge-record-details",
        "knowledge-record-id",
        "knowledge-kind",
        "knowledge-key",
        "knowledge-value",
        "knowledge-created-row",
        "knowledge-created",
        "knowledge-count-row",
        "knowledge-count",
        "knowledge-records",
        "knowledge-empty",
        "knowledge-truncated",
    }
    assert projection_ids <= set(parsed.elements_by_id)
    assert "hidden" in parsed.elements_by_id["list-projection"]
    assert "hidden" in parsed.elements_by_id["projection-added-row"]
    assert "hidden" in parsed.elements_by_id["projection-already-present-row"]
    assert "hidden" in parsed.elements_by_id["knowledge-projection"]
    assert "hidden" in parsed.elements_by_id["knowledge-created-row"]
    assert "hidden" in parsed.elements_by_id["knowledge-count-row"]
    assert "hidden" in parsed.elements_by_id["knowledge-empty"]
    assert "hidden" in parsed.elements_by_id["knowledge-truncated"]
    assert "Knowledge details" in document
    assert "workspace" not in document.lower().split("knowledge details", 1)[1]
    results = document.split('<section class="panel results"', 1)[1]
    assert "provenance" not in results.lower()
    assert "source_type" not in results
    assert "source_reference" not in results
    assert {"status", "route", "response", "error"} <= set(parsed.elements_by_id)
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
    send = script[script.index('form.addEventListener("submit"') :]
    assert send.index('proofInput.value = ""') < send.index("fetch(")
    assert ".textContent" in script
    assert "document.createElement" in script
    assert "replaceChildren" in script

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


def test_knowledge_assistance_is_separate_from_explicit_send() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    parsed = _parse(html)
    helper = html.split('id="knowledge-assistance"', 1)[1].split(
        '<form id="command-form">', 1
    )[0]
    command_form = html.split('<form id="command-form">', 1)[1].split("</form>", 1)[0]
    assert 'id="prepare-command" type="button"' in helper
    assert "assist-" not in command_form
    assert 'id="send-command" type="submit"' in command_form
    assert parsed.elements_by_id["preparation-error"]["role"] == "alert"
    assert parsed.elements_by_id["preparation-status"]["role"] == "status"
    assert parsed.elements_by_id["command-state"]["role"] == "status"
    for field in ("record-id", "key", "value", "source-type", "source-reference"):
        assert any(item.get("id") == f"assist-{field}" for item in parsed.textareas)
        assert f'for="assist-{field}"' in helper
        assert parsed.elements_by_id[f"assist-{field}"]["autocomplete"] == "off"
        assert parsed.elements_by_id[f"assist-{field}"].get("value") is None
    assert "including\n        provenance" in html
    assert "not verified identity or provenance" in html


def test_generated_assistance_commands_match_real_interpreter() -> None:
    # Node is an optional local verification tool, not a product dependency.
    node = shutil.which("node")
    if node is None:
        pytest.skip("Installed Node required for actual UI JavaScript verification")
    completed = subprocess.run(
        [node, "tests/browser/local_knowledge_command_assistance.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["passed"] > 0
    interpreter = DeterministicLocalCommandInterpreter()
    workspace = WorkspaceIdentity("sprint37-test-only")
    for vector in evidence["vectors"]:
        result = interpreter.interpret(vector["command"], workspace)
        assert result.status.value == "interpreted", vector["name"]
        intent = result.intent
        expected = vector["fields"]
        if vector["operation"] == "store":
            record = intent.record
            assert record.workspace is workspace
            assert record.kind.value == expected["kind"]
            for field in ("record_id", "key", "value"):
                assert getattr(record, field) == expected[field].strip()
            for field in ("source_type", "source_reference"):
                assert getattr(record.provenance, field) == expected[field].strip()
        elif vector["operation"] == "read":
            assert intent.record_id == expected["record_id"].strip()
        else:
            assert intent.key == expected["key"].strip()
            assert (intent.kind.value if intent.kind else "") == expected["kind"]


def test_browse_ui_vectors_match_real_interpreter_without_id_rewriting() -> None:
    from app.cognition.local_resolution.models import (
        BrowseKnowledgeRecordsQuery,
        ReadKnowledgeRecordQuery,
    )

    node = shutil.which("node")
    if node is None:
        pytest.skip("Installed Node required for actual UI JavaScript verification")
    completed = subprocess.run(
        [node, "tests/browser/local_knowledge_browse.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == 0
    assert {
        "preparation",
        "replacement",
        "states",
        "literal-metadata",
        "selection",
        "limits",
        "error-preservation",
        "stale-results",
        "no-fetch",
        "send",
        "pending",
        "regression",
        "invalid-projection",
    } <= set(evidence["categories"])
    assert {vector["operation"] for vector in evidence["vectors"]} == {
        "browse",
        "read",
    }
    interpreter = DeterministicLocalCommandInterpreter()
    for vector in evidence["vectors"]:
        result = interpreter.interpret(
            vector["command"], WorkspaceIdentity("s38-ui-test-only")
        )
        assert result.status.value == "interpreted", vector["name"]
        if vector["operation"] == "browse":
            assert type(result.intent) is BrowseKnowledgeRecordsQuery
        else:
            assert type(result.intent) is ReadKnowledgeRecordQuery
            assert result.intent.record_id == vector["record_id"], vector["name"]


def test_browse_preparation_controls_do_not_submit_or_add_assets() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    assert 'id="prepare-browse" type="button"' in html
    assert html.index('id="prepare-browse"') < html.index('<form id="command-form">')
    assert 'button.type = "button"' in script
    assert "prepareGuidedRecallRead(recordId)" in script
    assert "text: commandInput.value" in script
    assert "const recordId = record.record_id" in script
    assert "No knowledge records in this workspace." in script
    assert (
        "Showing up to 50 records by ID. More records exist; "
        "prepare the next page to continue."
    ) in script


def test_list_projection_script_has_closed_safe_rendering_contract() -> None:
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    rendering = script[
        script.index("function renderListProjection") : script.index(
            "function isKnowledgeRecord"
        )
    ]

    assert 'projection?.kind !== "list"' in rendering
    assert 'projection.operation === "add"' in rendering
    assert 'projection.operation === "read"' in rendering
    assert "Array.isArray" in rendering
    assert "projectionAddedRow.hidden = false" in rendering
    assert "projectionAlreadyPresentRow.hidden = false" in rendering
    assert "commandInput" not in rendering
    assert "responseOutput" not in rendering
    assert "innerHTML" not in rendering
    assert 'output.textContent = "—"' in script
    assert 'document.createElement("li")' in script
    assert "item.textContent = value" in script
    assert "projectionListId.textContent = projection.list_id" in rendering


def test_projection_hidden_state_overrides_visible_grid_layout() -> None:
    css = (ASSET_ROOT / "styles.css").read_text(encoding="utf-8")
    visible_rule = ".projection-row {\n  display: grid;"
    hidden_selector = (
        "#list-projection[hidden],\n"
        "#knowledge-projection[hidden],\n"
        ".knowledge-projection [hidden],\n"
        ".projection-row[hidden] {"
    )
    visible_position = css.index(visible_rule)
    hidden_position = css.index(hidden_selector)
    hidden_rule = css[hidden_position : css.index("}", hidden_position)]

    assert hidden_position > visible_position
    assert "display: none;" in hidden_rule


def test_all_projections_are_cleared_before_submit_can_exit_or_fetch() -> None:
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    submit = script.index('form.addEventListener("submit"')
    prevent = script.index("event.preventDefault()", submit)
    clear = script.index('clearDraftResults("Pending")', prevent)
    csrf = script.index("const csrfMeta", clear)
    fetch = script.index("fetch(", csrf)

    assert submit < prevent < clear < csrf < fetch
    draft_clearing = script[
        script.index("function clearDraftResults") : script.index(
            "function updatePreparationButton"
        )
    ]
    assert "clearAllProjections();" in draft_clearing
    assert "function clearAllProjections() {" in script
    clear_all = script[
        script.index("function clearAllProjections() {") : script.index(
            "function renderCollection"
        )
    ]
    assert "clearListProjection();" in clear_all
    assert "clearKnowledgeProjection();" in clear_all
    assert "function renderLocalFailure() {\n  clearAllProjections();" in script
    assert (
        "function renderListProjection(projection) {\n  clearListProjection();"
    ) in script


def test_knowledge_projection_has_closed_literal_rendering_contract() -> None:
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    rendering = script[
        script.index("function isKnowledgeRecord") : script.index(
            "function renderResult"
        )
    ]

    assert 'projection?.kind !== "knowledge"' in rendering
    assert 'projection.operation === "store"' in rendering
    assert 'projection.operation === "read"' in rendering
    assert 'projection.operation === "find"' in rendering
    assert '["fact", "concept", "state"].includes(record.kind)' in rendering
    assert 'typeof projection.created === "boolean"' in rendering
    assert 'typeof projection.truncated === "boolean"' in rendering
    assert 'knowledgeOperation.textContent = "Stored"' in rendering
    assert 'knowledgeOperation.textContent = "Read"' in rendering
    assert 'knowledgeOperation.textContent = "Find"' in rendering
    assert 'knowledgeOperation.textContent = "Found"' not in rendering
    assert (
        'knowledgeCreated.textContent = projection.created ? "Yes" : "No"' in rendering
    )
    assert "knowledgeCreated.textContent = String(projection.created)" not in rendering
    assert 'knowledgeCreated.textContent = ""' in rendering
    assert "knowledgeCreatedRow.hidden = true" in rendering
    assert "knowledgeCount.textContent = String(projection.records.length)" in rendering
    assert "for (const record of projection.records)" in rendering
    assert 'document.createElement("article")' in rendering
    assert 'document.createElement("dt")' in rendering
    assert 'document.createElement("dd")' in rendering
    assert "description.textContent = value" in rendering
    assert "knowledgeRecords.appendChild(article)" in rendering
    assert "JSON.stringify(record)" not in rendering
    assert "innerHTML" not in rendering


def test_empty_truncated_and_stale_knowledge_states_are_explicit() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    clearing = script[
        script.index("function clearKnowledgeProjection") : script.index(
            "function clearAllProjections"
        )
    ]

    assert "No matching knowledge records." in html
    assert "Showing the first 50 matching records." in html
    assert "knowledgeRecords.replaceChildren();" in clearing
    assert "knowledgeCreatedRow.hidden = true" in clearing
    assert "knowledgeEmpty.hidden = true" in clearing
    assert "knowledgeTruncated.hidden = true" in clearing
    assert "knowledgeEmpty.hidden = projection.records.length !== 0" in script
    assert "knowledgeTruncated.hidden = projection.truncated !== true" in script


def test_result_dispatch_clears_then_isolates_projection_families() -> None:
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    rendering = script[
        script.index("function renderResult") : script.index(
            "function renderLocalFailure"
        )
    ]

    assert rendering.index("clearAllProjections();") < rendering.index(
        'result.projection?.kind === "list"'
    )
    assert 'result.projection?.kind === "knowledge"' in rendering
    assert "renderListProjection(result.projection)" in rendering
    assert "renderKnowledgeProjection(result.projection)" in rendering


def test_guided_experience_shell_is_presentation_only() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    parsed = _parse(html)

    expected_ids = {
        "guided-experience",
        "guided-heading",
        "guided-help",
        "guided-status",
        "guided-reset",
        "guided-stages",
        "guided-capture",
        "guided-capture-state",
        "guided-recall",
        "guided-recall-state",
        "guided-follow-up",
        "guided-follow-up-state",
        "guided-verify",
        "guided-verify-state",
    }
    assert expected_ids <= set(parsed.elements_by_id)
    assert parsed.elements_by_id["guided-status"]["role"] == "status"
    assert parsed.elements_by_id["guided-capture"]["data-guide-state"] == "ready"
    for stage in ("recall", "follow-up", "verify"):
        assert (
            parsed.elements_by_id[f"guided-{stage}"]["data-guide-state"]
            == "not-started"
        )
    reset = next(
        button for button in parsed.buttons if button.get("id") == "guided-reset"
    )
    assert reset.get("type") == "button"
    assert html.index('id="guided-reset"') < html.index('<form id="command-form">')
    assert "Preparation never sends a request." in html
    assert "Guide progress exists only in this browser tab" in html
    assert "Send remains the governed execution boundary." in html

    for literal in (
        '"not-started"',
        '"ready"',
        '"prepared"',
        '"pending"',
        '"completed"',
        '"failed"',
        "function renderGuidedState",
        "function setGuidedStageState",
        "function resetGuidedExperience",
        "correlation: null",
        "guidedResetButton.disabled = pending",
    ):
        assert literal in script


def test_guided_experience_state_harness_has_zero_requests() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Installed Node required for Sprint 40 UI verification")
    completed = subprocess.run(
        [node, "tests/browser/local_guided_capture_recall_action.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == 0
    assert {
        "initial",
        "states",
        "validation",
        "reset",
        "editor-authority",
        "no-fetch",
    } == set(evidence["categories"])
    assert evidence["states"] == [
        "not-started",
        "ready",
        "prepared",
        "pending",
        "completed",
        "failed",
    ]


def test_guided_capture_recall_harness_uses_governed_results() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Installed Node required for Sprint 40 UI verification")

    completed = subprocess.run(
        [
            node,
            "tests/browser/local_guided_capture_recall_action.js",
            "--capture-recall",
        ],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)

    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == 7
    assert evidence["nativeBrowserVerified"] is False
    assert {
        "capture-prepare",
        "capture-send",
        "capture-result",
        "recall-query-prepare",
        "recall-query-send",
        "recall-query-result",
        "selection",
        "manual-editor",
        "mismatch",
        "recall-read-send",
        "recall-complete",
        "capture-replacement",
        "recall-replacement",
        "operation-replacement",
        "no-hidden-send",
    } == set(evidence["categories"])

    interpreter = DeterministicLocalCommandInterpreter()
    workspace = WorkspaceIdentity("sprint40-block-b-test-only")
    assert {vector["operation"] for vector in evidence["vectors"]} == {
        "store",
        "find",
        "read",
    }
    for vector in evidence["vectors"]:
        result = interpreter.interpret(vector["command"], workspace)
        assert result.status.value == "interpreted", vector["operation"]


def test_guided_follow_up_harness_and_interpreter_parity() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Installed Node required for Sprint 40 UI verification")
    completed = subprocess.run(
        [node, "tests/browser/local_guided_capture_recall_action.js", "--follow-up"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["passed"] == 134
    assert evidence["actualRequests"] == 0
    assert evidence["mockedFetchCalls"] == evidence["explicitSubmissions"] == 28
    assert evidence["nativeBrowserVerified"] is False
    assert {
        "precondition",
        "preparation",
        "delimiter-collision",
        "item-separator",
        "list-id-whitespace",
        "blank",
        "unicode",
        "whitespace",
        "pending",
        "added",
        "already-present",
        "manual-edit",
        "retry",
        "replacement",
        "malformed",
        "wrong-list",
        "absent-item",
        "exact-spelling",
        "failure",
        "unrelated",
        "wrong-operation",
        "network-failure",
        "reset",
        "no-hidden-send",
        "exact-editor",
        "prepared-edit",
        "operation-replacement",
        "types",
        "length",
        "unicode-rejection",
    } == set(evidence["categories"])

    interpreter = DeterministicLocalCommandInterpreter()
    workspace = WorkspaceIdentity("sprint40-block-c-test-only")
    for vector in evidence["vectors"]:
        result = interpreter.interpret(vector["command"], workspace)
        assert result.status.value == "interpreted"
        assert isinstance(result.intent, AddListItemsCommand)
        assert result.intent.list_id == vector["listId"]
        assert result.intent.items == (vector["expectedItem"],)

    # The first :: wins: without the UI guard the intended ID and item change.
    collision = interpreter.interpret(
        "list add project::tasks :: Call pharmacy tomorrow",
        workspace,
    )
    assert isinstance(collision.intent, AddListItemsCommand)
    assert collision.intent.list_id == "project"
    assert collision.intent.items == ("tasks :: Call pharmacy tomorrow",)


def test_follow_up_controls_are_preparatory_and_accessible() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="prepare-follow-up" type="button" disabled' in html
    assert html.index('id="prepare-follow-up"') < html.index('<form id="command-form">')
    for field in ("follow-up-list-id", "follow-up-item"):
        assert f'for="{field}"' in html
        assert f'id="{field}"' in html
    assert 'id="follow-up-error" role="alert"' in html


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
            "projection": {
                "kind": "list",
                "operation": "add",
                "list_id": "sprint34-b4",
                "added": ["alpha", "beta"],
                "already_present": [],
                "items": ["alpha", "beta"],
            },
        },
    )
    assert read == (
        200,
        {
            "success": True,
            "route": "local",
            "response": "List read locally.",
            "error": None,
            "projection": {
                "kind": "list",
                "operation": "read",
                "list_id": "sprint34-b4",
                "items": ["alpha", "beta"],
            },
        },
    )
    assert wrong_proof[0] == 403
    assert wrong_proof[1]["error"]["code"] == "access_denied"
    assert "projection" not in wrong_proof[1]
    assert wrong_csrf == (403, TRANSPORT_REJECTION)
    assert "projection" not in wrong_csrf[1]


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


def test_browse_after_ui_harness_and_real_interpreter_parity() -> None:
    from app.cognition.local_resolution.models import BrowseAfterKnowledgeRecordsQuery

    node = shutil.which("node")
    assert node is not None, "Node is required for Sprint 39 Block E verification"
    completed = subprocess.run(
        [node, "tests/browser/local_knowledge_browse_after.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == 0
    assert evidence["nativeKeyboardVerified"] is False
    assert {
        "initial-browse",
        "explicit-send",
        "continuation-render",
        "next-page",
        "prepare-no-fetch",
        "keyboard-focus",
        "stale-controls",
        "final-page",
        "read-continuation",
        "flow-101",
        "empty",
        "unicode-escaping",
        "length-boundaries",
        "failure-preservation",
        "pending",
        "disconnect-recovery",
        "visibility",
    } == set(evidence["categories"])
    interpreter = DeterministicLocalCommandInterpreter()
    lengths = set()
    for vector in evidence["vectors"]:
        command = vector["command"]
        assert len(command) <= 8192
        lengths.add(len(command))
        payload = json.loads(command.split(" :: ", 1)[1])
        assert payload == {"after_record_id": vector["anchor"]}
        result = interpreter.interpret(command, WorkspaceIdentity("s39-ui-only"))
        assert result.status.value == "interpreted"
        assert type(result.intent) is BrowseAfterKnowledgeRecordsQuery
        assert result.intent.after_record_id == vector["anchor"].strip()
    assert {8191, 8192} <= lengths


def test_browse_after_uses_existing_accessible_preparation_boundary() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    assert 'id="preparation-status" role="status"' in html
    assert 'id="preparation-error" role="alert"' in html
    action = script[
        script.index("function renderNextPageAction") : script.index(
            "function clearDraftResults"
        )
    ]
    assert 'button.type = "button"' in action
    assert "const anchor = records[records.length - 1].record_id" in action
    assert "prepareGuidedRecallQuery(" in action
    assert '"browse-after"' in action
    assert "{ after_record_id: anchor }" in action
    assert "fetch(" not in action
    assert "keydown" not in action and "keyup" not in action
    assert ".trim(" not in script and ".normalize(" not in script
    assert "No knowledge records after this ID in this workspace." in script


def test_guided_verify_harness_and_real_interpreter_parity() -> None:
    from app.cognition.local_resolution.models import ReadListItemsQuery

    node = shutil.which("node")
    assert node is not None, "Node is required for Block D verification"
    completed = subprocess.run(
        [node, "tests/browser/local_guided_capture_recall_action.js", "--verify"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["passed"] == 199
    assert evidence["actualRequests"] == evidence["hiddenRequests"] == 0
    assert evidence["mockedFetchCalls"] == evidence["explicitSubmissions"] == 41
    assert evidence["nativeBrowserVerified"] is False
    assert evidence["nativeKeyboardVerified"] is False
    assert {
        "precondition",
        "no-hidden-send",
        "exact-editor",
        "retained-context",
        "preparation",
        "stale-projection",
        "pending",
        "ascii",
        "completion",
        "stable",
        "missing-item",
        "wrong-list",
        "failure",
        "malformed",
        "unrelated",
        "wrong-operation",
        "network-failure",
        "manual-edit",
        "retry",
        "dependent-invalidation",
        "sharp-s",
        "sigma",
        "ligature",
        "dotted-i",
        "negative",
        "no-trimming",
        "no-normalization",
        "replacement",
        "reset",
    } == set(evidence["categories"])
    interpreter = DeterministicLocalCommandInterpreter()
    for vector in evidence["vectors"]:
        result = interpreter.interpret(
            vector["command"],
            WorkspaceIdentity("sprint40-block-d-test-only"),
        )
        assert result.status.value == "interpreted"
        assert isinstance(result.intent, ReadListItemsQuery)
        assert result.intent.list_id == vector["listId"]
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    button = _parse(html).elements_by_id["prepare-verification"]
    assert button["type"] == "button"
    assert button["aria-describedby"] == "verification-help"
    assert html.index('id="prepare-verification"') < html.index(
        '<form id="command-form">',
    )


def test_browser_casefold_matches_current_python_runtime() -> None:
    # Derive the complete non-identity mapping from this interpreter, including
    # supplementary planes. This also rejects extra mappings for identity points.
    mapping = {
        str(point): chr(point).casefold()
        for point in range(0x110000)
        if chr(point).casefold() != chr(point)
    }
    vectors = [
        ("GRAPES", "grapes"),
        ("Stra\u00dfe", "STRASSE"),
        ("\u03a3", "\u03c2"),
        ("\u03c2", "\u03c3"),
        ("o\ufb03ce", "OFFICE"),
        ("\u0130", "i\u0307"),
        ("\u212a", "k"),
        ("\u1e9e", "ss"),
        ("\U00010400", "\U00010428"),
        ("\u13a0", "\uab70"),
        ("\u00e9", "e\u0301"),
        ("grape", "grapes"),
        (" grapes", "grapes"),
        ("grapes\n", "grapes"),
        ("I", "\u0131"),
        ("\u0130", "i"),
        ("", ""),
        ("\ud800", "\ud800"),
        ("\U0001f347", "\U0001f347"),
        ("\ufeffgrapes", "grapes"),
    ]
    for point, folded in mapping.items():
        vectors.extend(((chr(int(point)), folded), (chr(int(point)), folded + "!")))
    node = shutil.which("node")
    assert node is not None, "Node is required for Python/browser casefold parity"
    completed = subprocess.run(
        [
            node,
            "tests/browser/local_guided_capture_recall_action.js",
            "--casefold-parity",
        ],
        input=json.dumps(vectors, ensure_ascii=True),
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["mapping"] == mapping
    assert len(evidence["results"]) == len(vectors)
    for (left, right), actual in zip(vectors, evidence["results"], strict=True):
        assert actual["folded"] == left.casefold()
        assert actual["equal"] is (left.casefold() == right.casefold())
    print(
        f"Python {platform.python_version()}: "
        f"{len(vectors)} casefold parity vectors PASS"
    )


def test_bounded_intent_preparer_purity_and_real_interpreter_parity() -> None:
    from app.cognition.local_resolution.models import (
        FindKnowledgeRecordsQuery,
        ReadListItemsQuery,
        StoreKnowledgeRecordCommand,
    )

    node = shutil.which("node")
    assert node is not None, "Node is required for Sprint 41 Block A verification"
    completed = subprocess.run(
        [node, "tests/browser/local_bounded_natural_language_intent_preparation.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == evidence["forbiddenAccesses"] == 0
    assert evidence["nativeBrowserVerified"] is False
    assert {
        "corpus",
        "wrappers",
        "generic-add",
        "generic-read",
        "capture-metadata",
        "no-invention",
        "kinds",
        "invalid-kind",
        "conflicts",
        "merge-trimming",
        "blank-explicit",
        "own-properties",
        "ordered-fields",
        "empty-placeholders",
        "rejection",
        "negation",
        "standalone",
        "list-validation",
        "item-validation",
        "python-whitespace",
        "explicit-surrogate",
        "multi-action-matrix",
        "quoted-matrix",
        "quote-escapes",
        "unlisted-guard",
        "literal-preservation",
        "input-length",
        "command-length",
        "json-escape-budget",
        "purity",
        "determinism",
        "closed-result",
        "serialization",
    } <= set(evidence["categories"])
    types = {
        "CAPTURE_KNOWLEDGE": StoreKnowledgeRecordCommand,
        "RECALL_KNOWLEDGE": FindKnowledgeRecordsQuery,
        "ADD_FOLLOW_UP": AddListItemsCommand,
        "READ_FOLLOW_UP": ReadListItemsQuery,
    }
    assert {vector["intent"] for vector in evidence["vectors"]} == set(types)
    interpreter = DeterministicLocalCommandInterpreter()
    workspace = WorkspaceIdentity("sprint41-block-a-synthetic")
    for vector in evidence["vectors"]:
        command, fields = vector["command"], vector["fields"]
        assert len(command) <= 8192
        result = interpreter.interpret(command, workspace)
        assert result.status.value == "interpreted", vector["intent"]
        intent = result.intent
        assert type(intent) is types[vector["intent"]]
        if isinstance(intent, StoreKnowledgeRecordCommand):
            record = intent.record
            assert record.workspace is workspace
            assert record.kind.value == fields["kind"]
            for field in ("record_id", "key", "value"):
                assert getattr(record, field) == fields[field].strip()
            for field in ("source_type", "source_reference"):
                assert getattr(record.provenance, field) == fields[field].strip()
            assert list(json.loads(command.split(" :: ", 1)[1])) == [
                "record_id",
                "kind",
                "key",
                "value",
                "source_type",
                "source_reference",
            ]
        elif isinstance(intent, FindKnowledgeRecordsQuery):
            assert intent.key == fields["key"].strip()
            assert (intent.kind.value if intent.kind is not None else None) == (
                fields.get("kind")
            )
            assert list(json.loads(command.split(" :: ", 1)[1])) == (
                ["key", "kind"] if "kind" in fields else ["key"]
            )
        elif isinstance(intent, AddListItemsCommand):
            assert intent.list_id == fields["list_id"].strip()
            assert intent.items == (fields["item"].strip(),)
        else:
            assert isinstance(intent, ReadListItemsQuery)
            assert intent.list_id == fields["list_id"].strip()
    print(
        f"Sprint 41 Block A: {len(evidence['vectors'])} real interpreter vectors PASS"
    )


def test_bounded_intent_ui_structure_and_accessible_controls() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    parsed = _parse(html)
    panel_start = html.index('<section id="natural-intent-panel"')
    panel_end = html.index("</section>", panel_start)
    panel = html[panel_start:panel_end]
    assert panel_end < html.index('id="assistance-heading"')
    assert panel_end < html.index('<form id="command-form">')
    assert "<form" not in panel
    assert parsed.elements_by_id["natural-intent-panel"]["aria-labelledby"] == (
        "natural-intent-heading"
    )
    natural_input = parsed.elements_by_id["natural-intent-input"]
    assert natural_input["rows"] == "4"
    assert natural_input["autocomplete"] == "off"
    assert natural_input["aria-describedby"] == "natural-intent-help"
    assert '<label for="natural-intent-input">' in panel
    assert "Deterministic preparation runs first." in panel
    assert "Send remains separate and governed." in panel
    assert parsed.elements_by_id["natural-intent-status"]["role"] == "status"
    assert "No natural-language proposal is active." in panel
    assert "hidden" in parsed.elements_by_id["natural-intent-result"]
    assert parsed.elements_by_id["natural-intent-clarification"]["role"] == "alert"
    for suffix in (
        "outcome",
        "detected-intent",
        "extracted-fields",
        "final-fields",
        "missing-fields",
        "invalid-fields",
        "conflicting-fields",
        "reason",
        "clarification",
    ):
        assert f'id="natural-intent-{suffix}"' in panel
    for action, label in (
        ("prepare", "Interpret / Prepare"),
        ("reject", "Reject proposal"),
    ):
        element_id = f"natural-intent-{action}"
        button = next(item for item in parsed.buttons if item["id"] == element_id)
        assert button["type"] == "button"
        assert f">{label}</button>" in panel
        assert "tabindex" not in button
    assert "disabled" in parsed.elements_by_id["natural-intent-reject"]
    for field in (
        "record-id",
        "kind",
        "key",
        "value",
        "source-type",
        "source-reference",
        "list-id",
        "item",
    ):
        element_id = f"natural-field-{field}"
        assert "hidden" in parsed.elements_by_id[f"{element_id}-row"]
        assert "disabled" in parsed.elements_by_id[element_id]
        assert parsed.elements_by_id[element_id]["autocomplete"] == "off"
        assert f'<label for="{element_id}">' in panel
    kind_select = panel.split('<select id="natural-field-kind"', 1)[1].split(
        "</select>",
        1,
    )[0]
    assert [part.split('"', 1)[0] for part in kind_select.split('value="')[1:]] == [
        "",
        "fact",
        "concept",
        "state",
    ]
    css = (ASSET_ROOT / "styles.css").read_text(encoding="utf-8")
    assert "#natural-intent-panel :focus-visible" in css
    assert "#natural-intent-panel [hidden]" in css


def test_bounded_intent_ui_literal_rendering_and_opt_in_boundary() -> None:
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    natural_ui = script[
        script.index("// Sprint 41 browser-only proposal lifecycle;") : script.index(
            "function setRequestPending(pending)"
        )
    ]
    assert "prepareBoundedNaturalLanguageIntent(" in natural_ui
    assert "if (!row.hidden && !input.disabled)" in natural_ui
    assert "commandInput.value = result.command" in natural_ui
    assert ".textContent =" in natural_ui
    for forbidden in (
        "innerHTML",
        "insertAdjacentHTML",
        "document.write",
        "localStorage",
        "sessionStorage",
        "indexedDB",
        ".submit(",
        ".requestSubmit(",
        "dispatchEvent(",
        "invalidateGuidedStage(",
    ):
        assert forbidden not in natural_ui
    assert natural_ui.count('fetch("/local/intent-preparation"') == 1
    assert "/local/command" not in natural_ui
    assert "body: JSON.stringify({ text: original })" in natural_ui
    assert "naturalProposal = null" in natural_ui
    assert "!naturalProposal.manuallyEdited" in natural_ui
    assert "commandInput.value === naturalProposal.generatedCommand" in natural_ui
    assert "naturalProposal.manuallyEdited = true" in script
    assert 'naturalIntentInput.addEventListener("input"' in natural_ui
    assert 'input.addEventListener("input", changed)' in natural_ui
    assert 'input.addEventListener("change", changed)' in natural_ui
    assert "if (!row.hidden && !input.disabled)" in natural_ui
    assert 'markNaturalProposalStale("manual")' in script
    assert 'setAttribute("data-natural-state", "stale")' in natural_ui
    prepared = natural_ui[natural_ui.index('if (result.outcome === "prepared")') :]
    assert (
        prepared.index("clearGuidedCorrelationForReplacement();")
        < (prepared.index("clearDraftResults();"))
        < prepared.index("commandInput.value = result.command;")
    )
    submit = script[script.index('form.addEventListener("submit"') :]
    assert "text: commandInput.value" in submit
    assert "prepareBoundedNaturalLanguageIntent(" not in submit
    assert submit.index("if (!csrfToken)") < submit.index("submitNaturalProposal();")
    assert submit.index("submitNaturalProposal();") < (
        submit.index('fetch("/local/command"')
    )
    assert '"Governed Send could not start; see Result. Editor retained."' in submit
    assert "Governed request settled; see Result" in submit
    # Every successful non-natural writer is guarded; natural write and Reject
    # have their own fresh/dismissal semantics.
    for writer in (
        "commandInput.value = `list read ${listId}`;",
        "commandInput.value = prepared.command;",
        "commandInput.value = preparedCommand;",
    ):
        assert "markNaturalProposalReplaced();\n  " + writer in script or (
            "markNaturalProposalReplaced();\n    " + writer in script
        )
    css = (ASSET_ROOT / "styles.css").read_text(encoding="utf-8")
    assert '[data-natural-state="stale"]' in css and "dashed" in css
    assert (
        "updateNaturalIntentControls();"
        in script[
            script.index("function setRequestPending(pending)") : script.index(
                'operationInput.addEventListener("change"'
            )
        ]
    )


def test_bounded_intent_ui_harness_preparation_rejection_and_pending() -> None:
    node = shutil.which("node")
    assert node is not None, "Node is required for Sprint 41 UI lifecycle verification"
    completed = subprocess.run(
        [node, "tests/browser/local_bounded_natural_language_intent_ui.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == 0
    assert evidence["forbiddenAccesses"] == evidence["formSubmissions"] == 0
    assert evidence["nativeBrowserVerified"] is False
    assert evidence["nativeKeyboardVerified"] is False
    assert evidence["preparationCalls"] > 0
    assert {
        "structure",
        "outside-form",
        "button-semantics",
        "initial",
        "real-entrypoint",
        "capture-clarification",
        "clarification-controls",
        "no-default-metadata",
        "explicit-action",
        "capture-prepared",
        "final-fields",
        "prepared-editor",
        "reject-available",
        "reject-discard",
        "reject-untouched",
        "unrelated-controls",
        "generic-clarification",
        "generic-prepared",
        "recall",
        "recall-kind",
        "visible-explicit-only",
        "explicit-read",
        "reject-manual",
        "reject-manual-state",
        "reject-edit-back",
        "reject-different-editor",
        "nonprepared-preservation",
        "no-hidden-command",
        "reject-nonprepared",
        "invalid-feedback",
        "conflict-feedback",
        "literal-rendering",
        "pending-lock",
        "pending-no-queue",
        "pending-restore",
        "zero-requests",
        "zero-submit",
        "no-provider-storage",
    } <= set(evidence["categories"])
    assert {
        "natural-input-stale",
        "semantic-custody",
        "reprepare-current",
        "optional-kind-stale",
        "clarification-stale",
        "unsupported-stale",
        "ignored-hidden-disabled",
        "manual-editor-stale",
        "manual-edit-back-stale",
        "reject-stale-manual",
        "reject-stale-untouched",
        "guided-clearing",
        "guided-dependents",
        "guided-nonreplacement",
        "nonreplacement-result-custody",
        "guided-completed-history",
        "no-invented-guide-transition",
        "draft-clearing",
        "replacement-matrix",
        "reject-replacement",
        "invalidation-zero-requests",
        "send-exact-editor",
        "send-no-reinterpret",
        "send-envelope",
        "submitted-state",
        "pending-event-custody",
        "settled-state",
        "pending-restored-after-send",
        "authoritative-result",
        "reject-submitted-zero-requests",
        "reject-submitted-editor",
        "submitted-stale-manual",
        "csrf-start-failure",
    } <= set(evidence["categories"])
    assert evidence["preparationInvalidationRequests"] == 0
    assert evidence["mockedFetchCalls"] == 5
    # Five explicit mocked Sends and one explicit Send prevented by missing CSRF.
    assert evidence["explicitSubmissions"] == 6


def test_sprint41_preparation_has_no_authority_inputs_or_transport() -> None:
    script = (ASSET_ROOT / "app.js").read_text(encoding="utf-8")
    pure = script[
        script.index("function prepareBoundedNaturalLanguageIntent(") : script.index(
            "const GUIDE_STAGES"
        )
    ]
    ui = script[
        script.index("// Sprint 41 browser-only proposal lifecycle;") : script.index(
            "function setRequestPending(pending)"
        )
    ]
    assert (
        "prepareBoundedNaturalLanguageIntent(naturalText, explicitFields = {})" in pure
    )
    assert (
        "prepareBoundedNaturalLanguageIntent(naturalIntentInput.value, explicitFields)"
        in ui
    )
    for authority in (
        "proofInput",
        "fallbackInput",
        "requested_workspace_id",
        "principal",
        "membership",
        "permissions",
        "actor",
        "localStorage",
        "sessionStorage",
    ):
        assert authority not in pure and authority not in ui
    assert "csrf" not in pure and "fetch(" not in pure
    assert ui.count('fetch("/local/intent-preparation"') == 1
    send = script[script.index('form.addEventListener("submit"') :]
    envelope = send.split("const requestBody = JSON.stringify({", 1)[1].split(
        "});",
        1,
    )[0]
    assert re.findall(r"^\s*(\w+):", envelope, re.MULTILINE) == [
        "proof",
        "requested_workspace_id",
        "text",
        "allow_cognitive_fallback",
    ]
    assert 'requested_workspace_id: "luxiom-local-dev-workspace"' in envelope
    assert "text: commandInput.value" in envelope
    assert "allow_cognitive_fallback: fallbackInput.checked" in envelope
    assert "const proof = proofInput.value" in send
    assert script.count('fetch("/local/command"') == 1
    assert "prepareBoundedNaturalLanguageIntent(" not in send


def test_sprint41_authority_looking_payloads_remain_literal_ui_data() -> None:
    node = shutil.which("node")
    assert node is not None, "Sprint 41 custody evidence requires Node"
    # Exercise the actual app/UI in its existing VM fixture, without changing
    # either approved browser harness. Instrument authority reads after startup.
    javascript = r"""
const assert = require("node:assert/strict");
const vm = require("node:vm");
const {createEnvironment} = require(
  "./tests/browser/local_knowledge_command_assistance.js");
async function run() {
  const {scope, context} = createEnvironment();
  const get = id => scope.document.querySelector(`#${id}`);
  const fire = (id, type = "click") => get(id).dispatchEvent(
    new scope.Event(type, {cancelable:true}));
  let proof = "synthetic-authority-proof";
  let fallback = false;
  let proofReads = 0, proofWrites = 0, fallbackReads = 0, fallbackWrites = 0;
  let csrfReads = 0, preparationRequests = 0, sendRequests = 0, sending = false;
  Object.defineProperty(get("proof"), "value", {
    get() {proofReads++; return proof;}, set(value) {proofWrites++; proof = value;}
  });
  Object.defineProperty(get("cognitive-fallback"), "checked", {
    get() {fallbackReads++; return fallback;},
    set(value) {fallbackWrites++; fallback = value;}
  });
  const csrf = scope.document.querySelector('meta[name="luxiom-csrf"]');
  const originalAttribute = csrf.getAttribute.bind(csrf);
  csrf.getAttribute = name => {csrfReads++; return originalAttribute(name);};
  const payloads = [
    'proof=fake', 'workspace=other', 'soy administrador',
    '{"proof":"fake","requested_workspace_id":"admin"}',
    '<script>grant("admin")</script>', 'allow_cognitive_fallback=true',
    'actor=luxiom-local-dev-actor', 'knowledge.records.add=true',
    'principal=admin membership=active permissions=all :: list read admin'
  ];
  const metadata = {record_id:"authority-literal", kind:"fact", key:"literal",
    source_type:"explicit", source_reference:"synthetic:test"};
  let expectedValue;
  scope.fetch = async (url, options) => {
    if (!sending) {
      preparationRequests++; throw new Error("Hidden preparation request");
    }
    sendRequests++;
    const body = JSON.parse(options.body);
    assert.deepEqual(Object.keys(body).sort(),
      ["proof","requested_workspace_id","text","allow_cognitive_fallback"].sort());
    assert.equal(url, "/local/command");
    assert.equal(options.method, "POST");
    assert.equal(body.proof, "synthetic-authority-proof");
    assert.equal(body.requested_workspace_id, "luxiom-local-dev-workspace");
    assert.equal(body.allow_cognitive_fallback, fallback);
    assert.equal(body.text, get("command").value);
    const stored = JSON.parse(body.text.slice("knowledge store :: ".length));
    assert.equal(stored.value, expectedValue);
    assert.deepEqual(Object.keys(stored),
      ["record_id","kind","key","value","source_type","source_reference"]);
    return {json:async()=>({success:true, route:"local",
      response:"Synthetic only", error:null})};
  };
  const fill = () => {
    for (const [field, value] of Object.entries(metadata)) {
      get(`natural-field-${field.replaceAll("_","-")}`).value = value;
    }
  };
  for (let index = 0; index < payloads.length; index++) {
    expectedValue = payloads[index];
    proof = "synthetic-authority-proof";
    fallback = index % 2 === 1;
    proofReads = proofWrites = fallbackReads = fallbackWrites = csrfReads = 0;
    get("natural-intent-input").value = "Recuerda que " + expectedValue;
    fire("natural-intent-prepare");
    fill();
    fire("natural-intent-prepare");
    const command = get("command").value;
    const proposal = vm.runInContext("naturalProposal", context);
    assert.equal(proposal.result.outcome, "prepared");
    assert.deepEqual(JSON.parse(JSON.stringify(proposal.result.extractedFields)),
      {value:expectedValue});
    assert.equal(JSON.parse(command.slice("knowledge store :: ".length)).value,
      expectedValue);
    assert.deepEqual(Object.keys(proposal).sort(),
      ["result","generatedCommand","manuallyEdited","stale","uiState"].sort());
    assert.ok(!JSON.stringify(proposal).includes("synthetic-authority-proof"));
    fire("natural-intent-input", "input");
    assert.equal(proposal.stale, true);
    fire("natural-intent-reject");
    assert.equal(get("command").value, "");
    assert.equal(vm.runInContext("naturalProposal", context), null);
    // Repeat explicit preparation after rejection; no retained authority/defaults.
    fire("natural-intent-prepare");
    fill();
    fire("natural-intent-prepare");
    assert.deepEqual([proofReads,proofWrites,fallbackReads,fallbackWrites,csrfReads],
      [0,0,0,0,0]);
    assert.equal(proof, "synthetic-authority-proof");
    assert.equal(fallback, index % 2 === 1);
    assert.equal(preparationRequests, 0);
    sending = true;
    fire("command-form", "submit");
    sending = false;
    for (let tick=0; tick<12; tick++) await Promise.resolve();
    assert.deepEqual([proofReads,proofWrites,fallbackReads,fallbackWrites,csrfReads],
      [1,1,1,0,1]);
    assert.equal(get("status").textContent, "Success");
    fire("natural-intent-reject");
  }
  return {literalVectors:payloads.length, preparationRequests, sendRequests,
    nativeBrowserVerified:false, nativeKeyboardVerified:false};
}
run().then(e => process.stdout.write(JSON.stringify(e)))
  .catch(e => {process.stderr.write(e.stack); process.exitCode=1;});
"""
    completed = subprocess.run(
        [node, "-e", javascript],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    evidence = json.loads(completed.stdout)
    assert evidence == {
        "literalVectors": 9,
        "preparationRequests": 0,
        "sendRequests": 9,
        "nativeBrowserVerified": False,
        "nativeKeyboardVerified": False,
    }


BLOCK_C_GOLDEN = json.loads(
    Path("tests/browser/local_model_intent_preparation_vectors.json").read_text(
        encoding="utf-8",
    ),
)


@pytest.mark.parametrize(
    "vector",
    BLOCK_C_GOLDEN,
    ids=[f"block-c-golden-{index}" for index in range(len(BLOCK_C_GOLDEN))],
)
def test_block_c_frozen_eligibility_golden(vector: dict[str, Any]) -> None:
    from app.cognition.intent_preparation.eligibility import assess_eligibility

    actual = assess_eligibility(vector["text"])
    assert actual.decision.value == vector["decision"]
    assert actual.reason == vector["reason"]


def test_block_c_browser_python_eligibility_and_unicode_parity() -> None:
    import unicodedata

    from app.cognition.intent_preparation.eligibility import assess_eligibility

    node = shutil.which("node")
    assert node is not None
    texts = [vector["text"] for vector in BLOCK_C_GOLDEN]
    # Exercise both sides of every Unicode category transition as standalone
    # negation boundaries, including supplementary and browser-new assignments.
    ranges = []
    start = None
    for point in range(0x110001):
        is_letter_number = point < 0x110000 and unicodedata.category(chr(point))[0] in (
            "L",
            "N",
        )
        if is_letter_number and start is None:
            start = point
        if not is_letter_number and start is not None:
            ranges.append([start, point - 1])
            start = None
    for left, right in ranges:
        for point in {max(0, left - 1), left, right, min(0x10FFFF, right + 1)}:
            character = chr(point)
            texts.extend((character + "no" + character, "si" + character))
    completed = subprocess.run(
        [node, "tests/browser/local_model_intent_preparation_ui.js", "--parity"],
        input=json.dumps(texts, ensure_ascii=True),
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["forbiddenAccesses"] == 0
    assert evidence["ranges"] == ranges
    assert len(evidence["classifications"]) == len(texts)
    for text, actual in zip(texts, evidence["classifications"], strict=True):
        python = assess_eligibility(text)
        assert actual == {
            "decision": python.decision.value,
            "reason": python.reason,
        }, repr(text)
    assert evidence["keywordText"] == ("abcdefghijklmnopqrstuvwxyzáéíóúüñİK")
    print(
        f"Block C: {len(texts)} browser/Python eligibility vectors and "
        "1114112 Unicode category points PASS",
    )


def test_block_c_consent_structure_and_accessibility() -> None:
    html = (ASSET_ROOT / "index.html").read_text(encoding="utf-8")
    parsed = _parse(html)
    consent = parsed.elements_by_id["local-model-consent"]
    assert consent["type"] == "checkbox"
    assert consent["autocomplete"] == "off"
    assert "checked" not in consent
    assert consent["aria-describedby"] == (
        "local-model-consent-help local-model-consent-status"
    )
    assert '<label class="checkbox" for="local-model-consent">' in html
    assert "Allow local model assistance" in html
    assert html.index('id="local-model-consent"') < html.index(
        '<form id="command-form">',
    )
    assert parsed.elements_by_id["local-model-consent-status"]["role"] == "status"
    assert "local interpretation assistance only" in html
    assert "grants no execution authority" in html
    assert "resets on refresh" in html
    assert "natural-intent-provenance" in parsed.elements_by_id


def test_block_c_real_ui_async_lifecycle_and_interpreter_parity() -> None:
    from app.cognition.local_resolution.models import (
        FindKnowledgeRecordsQuery,
        ReadListItemsQuery,
        StoreKnowledgeRecordCommand,
    )

    node = shutil.which("node")
    assert node is not None
    completed = subprocess.run(
        [node, "tests/browser/local_model_intent_preparation_ui.js"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )
    evidence = json.loads(completed.stdout)
    assert evidence["environment"] == "node-dom-double"
    assert evidence["actualRequests"] == evidence["forbiddenAccesses"] == 0
    assert evidence["implicitSubmissions"] == 0
    assert evidence["nativeBrowserVerified"] is False
    assert evidence["nativeKeyboardVerified"] is False
    assert evidence["goldenVectors"] == len(BLOCK_C_GOLDEN)
    assert evidence["passed"] > 400
    assert {
        "default-off",
        "startup-no-request",
        "session-reset",
        "no-persistence",
        "deterministic-first",
        "deterministic-prepared",
        "deterministic-clarification",
        "protected-zero-calls",
        "eligible-off",
        "one-request",
        "duplicate-no-request",
        "text-only",
        "transport",
        "literal-provenance",
        "capture-metadata",
        "clarification-editor-retained",
        "recall-exact-key",
        "recall-kind",
        "list-builders",
        "explicit-conflict",
        "failure-state",
        "closed-malformed",
        "wire-failure",
        "partial-clarification",
        "list-source-constraints",
        "reject-untouched",
        "reject-manual",
        "reject-edit-back",
        "stale-natural-edit-back",
        "stale-manual-edit-back",
        "stale-consent",
        "stale-reject",
        "stale-replacement",
        "stale-new-interpretation",
        "no-queued-request",
        "pending-slot-cleanup",
        "late-body-correlation",
        "send-exact-editor-envelope",
        "no-reinterpret-on-send",
        "zero-authority-access",
        "zero-implicit-send",
    } <= set(evidence["categories"])
    types = {
        "CAPTURE_KNOWLEDGE": StoreKnowledgeRecordCommand,
        "RECALL_KNOWLEDGE": FindKnowledgeRecordsQuery,
        "ADD_FOLLOW_UP": AddListItemsCommand,
        "READ_FOLLOW_UP": ReadListItemsQuery,
    }
    assert {vector["intent"] for vector in evidence["vectors"]} == set(types)
    interpreter = DeterministicLocalCommandInterpreter()
    workspace = WorkspaceIdentity("sprint42-block-c-synthetic")
    for vector in evidence["vectors"]:
        command, fields = vector["command"], vector["fields"]
        assert len(command) <= 8192
        result = interpreter.interpret(command, workspace)
        assert result.status.value == "interpreted", vector["name"]
        intent = result.intent
        assert type(intent) is types[vector["intent"]]
        if isinstance(intent, StoreKnowledgeRecordCommand):
            assert intent.record.workspace is workspace
            assert intent.record.kind.value == fields["kind"]
            for name in ("record_id", "key", "value"):
                assert getattr(intent.record, name) == fields[name]
            for name in ("source_type", "source_reference"):
                assert getattr(intent.record.provenance, name) == fields[name]
        elif isinstance(intent, FindKnowledgeRecordsQuery):
            assert intent.key == fields["key"]
            assert (intent.kind.value if intent.kind is not None else None) == (
                fields.get("kind")
            )
        elif isinstance(intent, AddListItemsCommand):
            assert intent.list_id == fields["list_id"]
            assert intent.items == (fields["item"],)
        else:
            assert intent.list_id == fields["list_id"]
    print(f"Block C: {evidence['passed']} async UI checks PASS")
