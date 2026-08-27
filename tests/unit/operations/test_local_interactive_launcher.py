import asyncio
import getpass
import importlib
import inspect
import sys
import threading
import tomllib
import urllib.request
import webbrowser
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

import pytest
import uvicorn

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LAUNCHER_PATH = REPOSITORY_ROOT / "scripts" / "launch_local_interactive.py"
CMD_PATH = REPOSITORY_ROOT / "scripts" / "launch_local_interactive.cmd"
UI_URL = "http://127.0.0.1:8765/local/ui"
PROOF_SENTINEL = "S34_B5_R1_SECRET_SENTINEL_DO_NOT_PRINT"


def _launcher():
    return importlib.import_module("scripts.launch_local_interactive")


def test_uvicorn_is_the_only_new_direct_runtime_dependency() -> None:
    project = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]

    assert project["dependencies"] == [
        "fastapi",
        "loguru",
        "pydantic",
        "pydantic-settings",
        "uvicorn",
    ]


def test_import_has_no_io_or_launch_side_effects(monkeypatch) -> None:
    observed: list[str] = []

    def record(name):
        def action(*args, **kwargs):
            del args, kwargs
            observed.append(name)
            raise AssertionError(name)

        return action

    monkeypatch.setattr(getpass, "getpass", record("prompt"))
    monkeypatch.setattr(Path, "mkdir", record("mkdir"))
    monkeypatch.setattr(uvicorn.Server, "run", record("server"))
    monkeypatch.setattr(urllib.request, "urlopen", record("network"))
    monkeypatch.setattr(webbrowser, "open", record("browser"))
    sys.modules.pop("scripts.launch_local_interactive", None)

    imported = importlib.import_module("scripts.launch_local_interactive")

    assert callable(imported.main)
    assert observed == []


def test_source_has_no_secret_or_path_override_backdoors() -> None:
    source = LAUNCHER_PATH.read_text(encoding="utf-8")

    assert "getpass.getpass(" in source
    assert "input(" not in source
    assert "runtime.start(" not in source
    assert "token_urlsafe" not in source
    assert "app.main" not in source
    assert "os.environ" not in source
    assert "os.getenv" not in source
    assert "expandvars" not in source
    for name in (
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "APPDATA",
        "LUXIOM_DB_PATH",
        "DATABASE_URL",
        "LOCAL_DB_PATH",
    ):
        assert name not in source


def test_database_path_uses_home_exact_components_and_creates_at_execution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher = _launcher()
    home = tmp_path / "person"
    repository = tmp_path / "repository"
    repository.mkdir()
    monkeypatch.setattr(launcher.Path, "home", classmethod(lambda cls: home))

    database_path = launcher._prepare_database_path(repository)

    assert database_path == (
        home
        / ".luxiom"
        / "development"
        / "local-interactive"
        / "luxiom-local.sqlite3"
    ).resolve()
    assert database_path.parent.is_dir()
    assert repository.resolve() not in database_path.parents


def test_database_path_revalidates_after_parent_creation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher = _launcher()
    home = tmp_path / "person"
    repository = tmp_path / "repository"
    repository.mkdir()
    monkeypatch.setattr(launcher.Path, "home", classmethod(lambda cls: home))
    calls: list[Path] = []
    real_validate = launcher._validate_external_database_path

    def observe(candidate: Path, root: Path) -> Path:
        calls.append(candidate)
        return real_validate(candidate, root)

    monkeypatch.setattr(launcher, "_validate_external_database_path", observe)

    launcher._prepare_database_path(repository)

    assert len(calls) == 2


def test_database_target_directory_conflict_fails_without_fallback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher = _launcher()
    home = tmp_path / "person"
    repository = tmp_path / "repository"
    repository.mkdir()
    target = (
        home
        / ".luxiom"
        / "development"
        / "local-interactive"
        / "luxiom-local.sqlite3"
    )
    target.mkdir(parents=True)
    monkeypatch.setattr(launcher.Path, "home", classmethod(lambda cls: home))

    with pytest.raises(launcher.LauncherOperationalError):
        launcher._prepare_database_path(repository)

    assert target.is_dir()


def test_existing_database_file_is_reused(tmp_path: Path, monkeypatch) -> None:
    launcher = _launcher()
    home = tmp_path / "person"
    repository = tmp_path / "repository"
    repository.mkdir()
    target = (
        home
        / ".luxiom"
        / "development"
        / "local-interactive"
        / "luxiom-local.sqlite3"
    )
    target.parent.mkdir(parents=True)
    target.write_bytes(b"existing")
    monkeypatch.setattr(launcher.Path, "home", classmethod(lambda cls: home))

    assert launcher._prepare_database_path(repository) == target.resolve()
    assert target.read_bytes() == b"existing"


class _Response:
    def __init__(self, status: int, final_url: str = UI_URL) -> None:
        self.status = status
        self.final_url = final_url

    def geturl(self) -> str:
        return self.final_url

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        del args


def _configure_main(
    monkeypatch,
    tmp_path: Path,
    *,
    start: bool = True,
    readiness: list[int | BaseException] | None = None,
    browser_result=True,
    run_error: BaseException | None = None,
    run_error_after_start: BaseException | None = None,
    run_error_after_readiness: BaseException | None = None,
    exit_after_start: bool = False,
):
    launcher = _launcher()
    proof = PROOF_SENTINEL
    database_path = tmp_path / "outside" / "luxiom-local.sqlite3"
    observed = SimpleNamespace(
        runtime_calls=[],
        app_calls=[],
        config_calls=[],
        browser_calls=[],
        request_calls=[],
        run_thread=None,
        should_exit_during_run=None,
        events=None,
        thread_calls=[],
        server_instances=[],
    )
    browser_attempted = threading.Event()
    real_thread = threading.Thread
    readiness_values = list(readiness if readiness is not None else [200])

    class FakeRuntime:
        def __init__(self, path, supplied_proof) -> None:
            observed.runtime_calls.append((path, supplied_proof))
            self.state = launcher.LocalInteractiveRuntimeState.NEW
            self.gateway = object()
            self.csrf_token = "distinctive-csrf-sentinel"

    def fake_app(runtime):
        observed.app_calls.append(runtime)
        return object()

    class FakeConfig:
        def __init__(self, app, **kwargs) -> None:
            observed.config_calls.append((app, kwargs))

    class FakeServer:
        def __init__(self, config, started_event, shutdown_requested_event) -> None:
            self.config = config
            self.started_event = started_event
            self.shutdown_requested_event = shutdown_requested_event
            observed.events = (started_event, shutdown_requested_event)
            observed.server_instances.append(self)

        def run(self) -> None:
            observed.run_thread = threading.current_thread()
            if run_error is not None:
                raise run_error
            if not start:
                return
            self.started_event.set()
            if run_error_after_start is not None:
                raise run_error_after_start
            if exit_after_start:
                return
            for _ in range(200):
                if (
                    browser_attempted.wait(timeout=0.01)
                    or self.shutdown_requested_event.is_set()
                ):
                    break
            observed.should_exit_during_run = (
                self.shutdown_requested_event.is_set()
            )
            if run_error_after_readiness is not None:
                raise run_error_after_readiness

    def fake_urlopen(request, *, timeout):
        observed.request_calls.append((request, timeout))
        value = readiness_values.pop(0) if readiness_values else URLError("not ready")
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, tuple):
            return _Response(*value)
        return _Response(value)

    def fake_browser(url):
        observed.browser_calls.append(url)
        browser_attempted.set()
        if isinstance(browser_result, BaseException):
            raise browser_result
        return browser_result

    def recording_thread(*args, **kwargs):
        observed.thread_calls.append((args, kwargs))
        return real_thread(*args, **kwargs)

    monkeypatch.setattr(launcher.getpass, "getpass", lambda prompt: proof)
    monkeypatch.setattr(
        launcher,
        "_prepare_database_path",
        lambda repository_root: database_path,
    )
    monkeypatch.setattr(launcher, "LocalInteractiveRuntime", FakeRuntime)
    monkeypatch.setattr(launcher, "create_local_interactive_app", fake_app)
    monkeypatch.setattr(launcher.uvicorn, "Config", FakeConfig)
    monkeypatch.setattr(launcher, "_LocalInteractiveServer", FakeServer)
    monkeypatch.setattr(launcher.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(launcher.webbrowser, "open", fake_browser)
    monkeypatch.setattr(launcher, "_wait", lambda stop, seconds: stop.is_set())
    monkeypatch.setattr(launcher.threading, "Thread", recording_thread)
    return launcher, observed, proof, database_path


def test_main_builds_one_new_runtime_one_app_and_fixed_uvicorn(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher, observed, proof, database_path = _configure_main(
        monkeypatch,
        tmp_path,
    )

    assert launcher.main() == 0

    assert observed.runtime_calls == [(database_path, proof)]
    assert len(observed.app_calls) == 1
    assert len(observed.config_calls) == 1
    _, config = observed.config_calls[0]
    assert config == {
        "host": "127.0.0.1",
        "port": 8765,
        "reload": False,
        "workers": 1,
        "lifespan": "on",
    }
    assert observed.run_thread is threading.main_thread()
    assert observed.browser_calls == [UI_URL]


def test_readiness_uses_exact_get_only_after_own_server_started(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher, observed, _, _ = _configure_main(monkeypatch, tmp_path)

    assert launcher.main() == 0

    assert len(observed.request_calls) == 1
    request, _ = observed.request_calls[0]
    assert request.full_url == UI_URL
    assert request.get_method() == "GET"
    assert request.headers == {}


def test_never_started_server_does_not_poll_or_open_browser(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher, observed, _, _ = _configure_main(
        monkeypatch,
        tmp_path,
        start=False,
    )

    assert launcher.main() == 1
    assert observed.request_calls == []
    assert observed.browser_calls == []


def test_system_exit_is_failure_and_discloses_no_proof(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    launcher, observed, proof, _ = _configure_main(
        monkeypatch,
        tmp_path,
        run_error=SystemExit(1),
    )

    assert launcher.main() == 1
    output = capsys.readouterr().out
    assert proof not in output
    assert observed.request_calls == []
    assert observed.browser_calls == []


def test_actual_thread_arguments_have_secret_free_object_graph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher, observed, proof, database_path = _configure_main(
        monkeypatch,
        tmp_path,
    )

    assert launcher.main() == 0
    assert len(observed.thread_calls) == 1
    positional, keywords = observed.thread_calls[0]
    assert positional == ()
    assert keywords["target"] is launcher._readiness_and_browser_worker
    assert keywords["target"].__closure__ is None
    worker_args = keywords["args"]
    assert len(worker_args) == 4
    event_type = type(threading.Event())
    assert all(type(value) is event_type for value in worker_args)
    assert all(set(vars(value)) == {"_cond", "_flag"} for value in worker_args)

    forbidden = {
        proof,
        database_path,
        observed.runtime_calls[0][0],
        observed.app_calls[0],
        observed.server_instances[0],
        observed.server_instances[0].config,
        observed.app_calls[0].gateway,
        observed.app_calls[0].csrf_token,
    }
    assert all(value not in forbidden for value in worker_args)
    assert all(
        owned not in forbidden
        for event in worker_args
        for owned in vars(event).values()
    )


def test_system_exit_after_started_is_failure(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    launcher, observed, proof, _ = _configure_main(
        monkeypatch,
        tmp_path,
        readiness=[URLError("must not become ready")],
        run_error_after_start=SystemExit(1),
    )

    assert launcher.main() == 1
    worker_args = observed.thread_calls[0][1]["args"]
    assert worker_args[0].is_set()
    assert worker_args[2].is_set()
    assert not worker_args[3].is_set()
    assert observed.browser_calls == []
    assert proof not in capsys.readouterr().out


@pytest.mark.parametrize("browser_result", (True, False))
def test_system_exit_after_ready_overrides_browser_state(
    tmp_path: Path,
    monkeypatch,
    capsys,
    browser_result: bool,
) -> None:
    launcher, observed, proof, _ = _configure_main(
        monkeypatch,
        tmp_path,
        browser_result=browser_result,
        run_error_after_readiness=SystemExit(1),
    )

    assert launcher.main() == 1
    worker_args = observed.thread_calls[0][1]["args"]
    assert worker_args[0].is_set()
    assert worker_args[2].is_set()
    assert worker_args[3].is_set()
    assert not worker_args[1].is_set()
    assert observed.browser_calls == [UI_URL]
    assert proof not in capsys.readouterr().out


@pytest.mark.parametrize("status", (201, 302, 403, 404, 500))
def test_only_http_200_is_ready_and_timeout_requests_shutdown(
    tmp_path: Path,
    monkeypatch,
    status: int,
) -> None:
    launcher, observed, _, _ = _configure_main(
        monkeypatch,
        tmp_path,
        readiness=[status] * 50,
    )

    assert launcher.main() == 1
    assert len(observed.request_calls) == 50
    assert observed.browser_calls == []
    assert observed.should_exit_during_run is True


def test_connection_failures_use_fifty_attempt_limit(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    launcher, observed, proof, _ = _configure_main(
        monkeypatch,
        tmp_path,
        readiness=[URLError("foreign service") for _ in range(50)],
    )

    assert launcher.main() == 1
    assert len(observed.request_calls) == 50
    assert observed.browser_calls == []
    assert proof not in capsys.readouterr().out


def test_followed_redirect_to_200_is_not_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher, observed, _, _ = _configure_main(
        monkeypatch,
        tmp_path,
        readiness=[(200, "http://127.0.0.1:8765/other")] * 50,
    )

    assert launcher.main() == 1
    assert len(observed.request_calls) == 50
    assert observed.browser_calls == []
    assert observed.events[1].is_set()


def test_server_exit_after_start_before_readiness_is_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launcher, observed, _, _ = _configure_main(
        monkeypatch,
        tmp_path,
        exit_after_start=True,
    )

    assert launcher.main() == 1
    assert observed.browser_calls == []


@pytest.mark.parametrize("browser_result", (False, RuntimeError("no browser")))
def test_browser_failure_keeps_server_running_and_prints_safe_url(
    tmp_path: Path,
    monkeypatch,
    capsys,
    browser_result,
) -> None:
    launcher, observed, proof, _ = _configure_main(
        monkeypatch,
        tmp_path,
        browser_result=browser_result,
    )

    assert launcher.main() == 0

    output = capsys.readouterr().out
    assert UI_URL in output
    assert "Open this address manually" in output
    assert proof not in output
    assert observed.should_exit_during_run is False
    assert not observed.events[1].is_set()


def test_path_failure_is_sanitized_and_starts_nothing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    launcher = _launcher()
    proof = "path-failure-proof"
    monkeypatch.setattr(launcher.getpass, "getpass", lambda prompt: proof)
    monkeypatch.setattr(
        launcher,
        "_prepare_database_path",
        lambda root: (_ for _ in ()).throw(
            launcher.LauncherOperationalError("private path detail")
        ),
    )
    monkeypatch.setattr(
        launcher,
        "LocalInteractiveRuntime",
        lambda *args: pytest.fail("runtime constructed"),
    )

    assert launcher.main() == 1
    output = capsys.readouterr().out
    assert proof not in output
    assert "private path detail" not in output


def test_parent_creation_failure_is_sanitized(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    launcher = _launcher()
    proof = PROOF_SENTINEL
    home = tmp_path / "person"
    monkeypatch.setattr(launcher.Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(
        launcher.Path,
        "mkdir",
        lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("private")),
    )
    monkeypatch.setattr(launcher.getpass, "getpass", lambda prompt: proof)
    monkeypatch.setattr(
        launcher,
        "LocalInteractiveRuntime",
        lambda *args: pytest.fail("runtime constructed"),
    )

    assert launcher.main() == 1
    output = capsys.readouterr().out
    assert proof not in output
    assert "private" not in output


def test_post_creation_redirection_is_rejected(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    launcher = _launcher()
    repository = tmp_path / "repository"
    repository.mkdir()
    candidate = (
        tmp_path
        / "person"
        / ".luxiom"
        / "development"
        / "local-interactive"
        / "luxiom-local.sqlite3"
    )
    monkeypatch.setattr(
        launcher.Path,
        "home",
        classmethod(lambda cls: tmp_path / "person"),
    )
    calls = 0

    def redirect_after_creation(path: Path, root: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == 1:
            return candidate
        raise launcher.LauncherOperationalError("The database location is unavailable.")

    monkeypatch.setattr(
        launcher,
        "_validate_external_database_path",
        redirect_after_creation,
    )
    monkeypatch.setattr(launcher.getpass, "getpass", lambda prompt: PROOF_SENTINEL)
    monkeypatch.setattr(
        launcher,
        "LocalInteractiveRuntime",
        lambda *args: pytest.fail("runtime constructed"),
    )

    monkeypatch.setattr(launcher, "_repository_root", lambda: repository)
    assert launcher.main() == 1
    assert calls == 2
    assert PROOF_SENTINEL not in capsys.readouterr().out


def test_worker_signature_and_closure_are_secret_free() -> None:
    launcher = _launcher()
    worker = launcher._readiness_and_browser_worker

    assert list(inspect.signature(worker).parameters) == [
        "started_event",
        "shutdown_requested_event",
        "session_stop_event",
        "ready_event",
    ]
    assert worker.__closure__ is None
    assert "server" not in inspect.signature(worker).parameters


def test_uvicorn_adapter_signals_start_and_delegates_tick(monkeypatch) -> None:
    launcher = _launcher()
    started_event = threading.Event()
    shutdown_event = threading.Event()
    calls: list[object] = []

    async def parent_startup(self, sockets=None):
        calls.append(("startup", sockets))
        self.started = True

    async def parent_tick(self, counter):
        calls.append(("tick", counter))
        return True

    monkeypatch.setattr(uvicorn.Server, "startup", parent_startup)
    monkeypatch.setattr(uvicorn.Server, "on_tick", parent_tick)
    server = launcher._LocalInteractiveServer(
        object(), started_event, shutdown_event
    )

    asyncio.run(server.startup(sockets=[]))
    shutdown_event.set()
    assert asyncio.run(server.on_tick(7)) is True
    assert started_event.is_set()
    assert server.should_exit is True
    assert calls == [("startup", []), ("tick", 7)]


def test_launcher_source_has_fixed_readiness_bounds() -> None:
    launcher = _launcher()

    assert launcher.READINESS_INTERVAL_SECONDS == 0.1
    assert launcher.READINESS_MAX_ATTEMPTS == 50
    assert launcher.UI_URL == UI_URL


def test_cmd_is_relative_quoted_secret_free_and_preserves_exit_code() -> None:
    command = CMD_PATH.read_text(encoding="utf-8")
    lowered = command.lower()

    assert "%~dp0" in command
    assert ".venv\\Scripts\\python.exe" in command
    assert "scripts\\launch_local_interactive.py" in command
    assert '"%PYTHON_EXE%"' in command
    assert 'if not exist "%PYTHON_EXE%"' in command
    assert "%ERRORLEVEL%" in command
    assert "exit /b %EXIT_CODE%" in command
    assert "C:\\PROYECTOS\\JARVIS-OS" not in command
    assert "proof" not in lowered
    assert "csrf" not in lowered
    assert "pip install" not in lowered
    assert "uv sync" not in lowered
    assert "poetry install" not in lowered
    assert "npm install" not in lowered
