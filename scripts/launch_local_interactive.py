"""Windows development launcher for the governed local interactive app."""

from __future__ import annotations

import getpass
import threading
import urllib.request
import webbrowser
from pathlib import Path
from urllib.error import HTTPError, URLError

import uvicorn

from app.api.interactive import create_local_interactive_app
from app.operations.local_interactive_runtime import (
    LocalInteractiveRuntime,
    LocalInteractiveRuntimeError,
    LocalInteractiveRuntimeState,
)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8765
UI_URL = "http://127.0.0.1:8765/local/ui"
READINESS_INTERVAL_SECONDS = 0.1
READINESS_MAX_ATTEMPTS = 50

_STARTUP_FAILURE = "LUXIOM local development runtime could not start."
_READINESS_FAILURE = "LUXIOM local development runtime did not become ready."


class LauncherOperationalError(RuntimeError):
    """Represent a sanitized expected launcher failure."""


class _LocalInteractiveServer(uvicorn.Server):
    """Bridge Uvicorn lifecycle state to secret-free launcher signals."""

    def __init__(
        self,
        config: uvicorn.Config,
        started_event: threading.Event,
        shutdown_requested_event: threading.Event,
    ) -> None:
        super().__init__(config)
        self._started_event = started_event
        self._shutdown_requested_event = shutdown_requested_event

    async def startup(self, sockets=None) -> None:
        await super().startup(sockets=sockets)
        if self.started:
            self._started_event.set()

    async def on_tick(self, counter: int) -> bool:
        if self._shutdown_requested_event.is_set():
            self.should_exit = True
        return await super().on_tick(counter)


def _repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _validate_external_database_path(
    candidate: Path,
    repository_root: Path,
) -> Path:
    resolved_repository = repository_root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    if (
        not resolved_candidate.is_absolute()
        or resolved_candidate == resolved_repository
        or resolved_repository in resolved_candidate.parents
        or resolved_candidate.is_dir()
    ):
        raise LauncherOperationalError("The database location is unavailable.")
    return resolved_candidate


def _prepare_database_path(repository_root: Path) -> Path:
    try:
        candidate = (
            Path.home()
            / ".luxiom"
            / "development"
            / "local-interactive"
            / "luxiom-local.sqlite3"
        )
        validated = _validate_external_database_path(candidate, repository_root)
        validated.parent.mkdir(parents=True, exist_ok=True)
        return _validate_external_database_path(candidate, repository_root)
    except LauncherOperationalError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise LauncherOperationalError(
            "The database location is unavailable."
        ) from error


def _wait(stop_event: threading.Event, seconds: float) -> bool:
    return stop_event.wait(seconds)


def _response_is_ready(response: object) -> bool:
    status = getattr(response, "status", None)
    if status != 200:
        return False
    get_url = getattr(response, "geturl", None)
    return not callable(get_url) or get_url() == UI_URL


def _print_manual_browser_instructions() -> None:
    print("LUXIOM is available at:")
    print(UI_URL)
    print("Open this address manually in your browser.")


def _readiness_and_browser_worker(
    started_event: threading.Event,
    shutdown_requested_event: threading.Event,
    session_stop_event: threading.Event,
    ready_event: threading.Event,
) -> None:
    while not started_event.is_set():
        if _wait(session_stop_event, READINESS_INTERVAL_SECONDS):
            return

    for attempt in range(READINESS_MAX_ATTEMPTS):
        if session_stop_event.is_set():
            return
        request = urllib.request.Request(UI_URL, method="GET")
        try:
            with urllib.request.urlopen(
                request,
                timeout=READINESS_INTERVAL_SECONDS,
            ) as response:
                if _response_is_ready(response):
                    ready_event.set()
                    try:
                        opened = webbrowser.open(UI_URL)
                    except Exception:
                        opened = False
                    if not opened:
                        _print_manual_browser_instructions()
                    return
        except (HTTPError, URLError, OSError, TimeoutError):
            pass
        if attempt + 1 < READINESS_MAX_ATTEMPTS and _wait(
            session_stop_event,
            READINESS_INTERVAL_SECONDS,
        ):
            return

    print(_READINESS_FAILURE)
    shutdown_requested_event.set()


def main() -> int:
    """Run one local interactive development session."""

    try:
        development_proof = getpass.getpass("Development proof: ")
        database_path = _prepare_database_path(_repository_root())
        runtime = LocalInteractiveRuntime(database_path, development_proof)
        if runtime.state is not LocalInteractiveRuntimeState.NEW:
            raise LauncherOperationalError("The runtime is unavailable.")
        app = create_local_interactive_app(runtime)
        config = uvicorn.Config(
            app,
            host=SERVER_HOST,
            port=SERVER_PORT,
            reload=False,
            workers=1,
            lifespan="on",
        )
        started_event = threading.Event()
        shutdown_requested_event = threading.Event()
        session_stop_event = threading.Event()
        ready_event = threading.Event()
        server = _LocalInteractiveServer(
            config,
            started_event,
            shutdown_requested_event,
        )
    except (EOFError, KeyboardInterrupt):
        print(_STARTUP_FAILURE)
        return 1
    except (
        LauncherOperationalError,
        LocalInteractiveRuntimeError,
        OSError,
        ValueError,
    ):
        print(_STARTUP_FAILURE)
        return 1

    helper = threading.Thread(
        target=_readiness_and_browser_worker,
        args=(
            started_event,
            shutdown_requested_event,
            session_stop_event,
            ready_event,
        ),
        name="luxiom-local-readiness",
    )

    print("LUXIOM local development runtime")
    print("Press Ctrl+C to stop.")
    helper.start()
    server_error = False
    try:
        server.run()
    except KeyboardInterrupt:
        pass
    except (LocalInteractiveRuntimeError, OSError, SystemExit):
        server_error = True
    finally:
        session_stop_event.set()
        helper.join()

    if server_error or not ready_event.is_set():
        if not shutdown_requested_event.is_set():
            print(_STARTUP_FAILURE)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
