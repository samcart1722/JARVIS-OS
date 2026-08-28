import importlib
from pathlib import Path

import pytest


def _demo():
    return importlib.import_module("app.operations.local_interactive_demo_runtime")


def test_demo_runtime_import_and_fixed_contract() -> None:
    demo = _demo()

    assert demo.DEMO_WORKSPACE.workspace_id == "luxiom-local-dev-workspace"
    assert demo.DURABILITY_ADD == (
        "list add sprint34-durability-proof :: alpha | beta"
    )
    assert demo.DURABILITY_READ == "list read sprint34-durability-proof"
    assert "production" not in repr(demo.DEMO_PROOF).lower()


def test_database_path_must_be_explicit_external_file(tmp_path: Path) -> None:
    demo = _demo()
    repository = tmp_path / "repository"
    repository.mkdir()

    with pytest.raises(demo.DemoOperationalError):
        demo.validate_demo_database(repository / "inside.sqlite3", repository)
    with pytest.raises(demo.DemoOperationalError):
        demo.validate_demo_database(repository.parent, repository)
    with pytest.raises(demo.DemoOperationalError):
        demo.validate_demo_database(Path("relative.sqlite3"), repository)

    external = tmp_path / "external" / "demo.sqlite3"
    assert demo.validate_demo_database(external, repository) == external.resolve()


def test_actual_http_durability_across_fresh_runtimes(tmp_path: Path) -> None:
    demo = _demo()
    database = tmp_path / "durability.sqlite3"

    assert demo.run_durability_write(database) == demo.ADD_SUCCESS
    response, items = demo.run_durability_read_and_observe(database)

    assert response == demo.READ_SUCCESS
    assert items == ("alpha", "beta")


def test_historical_demo_envelope_allows_only_projection_addition() -> None:
    demo = _demo()

    projected = {
        **demo.ADD_SUCCESS,
        "projection": {
            "kind": "list",
            "operation": "add",
            "list_id": "sprint34-durability-proof",
            "added": ["alpha", "beta"],
            "already_present": [],
            "items": ["alpha", "beta"],
        },
    }

    assert demo._historical_demo_response(projected) == demo.ADD_SUCCESS

    with pytest.raises(demo.DemoOperationalError):
        demo._historical_demo_response(
            {
                **demo.ADD_SUCCESS,
                "metadata": {"unexpected": True},
            }
        )

    missing_historical_field = dict(demo.ADD_SUCCESS)
    del missing_historical_field["error"]

    with pytest.raises(demo.DemoOperationalError):
        demo._historical_demo_response(missing_historical_field)


def test_active_runtime_membership_denial_is_governed_http(tmp_path: Path) -> None:
    demo = _demo()

    assert demo.run_membership_denial(tmp_path / "membership.sqlite3") == (
        403,
        demo.MEMBERSHIP_DENIAL,
    )


def test_active_runtime_permission_denial_is_governed_http(tmp_path: Path) -> None:
    demo = _demo()

    assert demo.run_permission_denial(tmp_path / "permission.sqlite3") == (
        403,
        demo.PERMISSION_DENIAL,
    )


def test_http_payload_and_delivered_csrf_are_exact(tmp_path: Path) -> None:
    demo = _demo()
    with demo.DemoInteractiveSession(tmp_path / "payload.sqlite3") as session:
        assert session.csrf_source == "GET /local/ui"
        assert session.payload(demo.DURABILITY_READ) == {
            "proof": demo.DEMO_PROOF,
            "requested_workspace_id": "luxiom-local-dev-workspace",
            "text": "list read sprint34-durability-proof",
            "allow_cognitive_fallback": False,
        }
        assert demo.DEMO_PROOF not in repr(session)


def test_direct_observation_occurs_only_after_http_session_closes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    demo = _demo()
    calls = []

    class Session:
        runtime = type(
            "Runtime",
            (),
            {"state": demo.LocalInteractiveRuntimeState.CLOSED},
        )()

        def __init__(self, path) -> None:
            calls.append(("construct", path))

        def __enter__(self):
            calls.append("enter")
            return self

        def post(self, text):
            calls.append(("http", text))
            return 200, demo.READ_SUCCESS

        def __exit__(self, *args):
            del args
            calls.append("close")

    monkeypatch.setattr(demo, "DemoInteractiveSession", Session)
    monkeypatch.setattr(
        demo,
        "observe_durable_items",
        lambda path: (calls.append(("observe", path)) or ("alpha", "beta")),
    )

    demo.run_durability_read_and_observe(tmp_path / "durability.sqlite3")
    assert calls[1:] == [
        "enter",
        ("http", demo.DURABILITY_READ),
        "close",
        ("observe", (tmp_path / "durability.sqlite3").resolve()),
    ]


def test_fixture_helpers_use_narrow_storage_apis() -> None:
    demo = _demo()
    source = Path(demo.__file__).read_text(encoding="utf-8")

    assert ".deactivate(" in source
    assert ".revoke(" in source
    assert "execute(" not in source
    assert "SELECT " not in source
    assert "UPDATE " not in source
    assert "DELETE " not in source
