"""Run the bounded Sprint 34 local interactive operational proof."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.operations.local_interactive_demo_runtime import (
    DemoOperationalError,
    run_durability_read_and_observe,
    run_durability_write,
    run_membership_denial,
    run_permission_denial,
    validate_demo_database,
)

PHASES = (
    "durability-write",
    "durability-read",
    "membership-denial",
    "permission-denial",
)
CHILD_TIMEOUT_SECONDS = 60


def _repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["DEBUG"] = "false"
    return environment


def _run_child(phase: str, database_path: Path) -> bool:
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--internal-phase",
                phase,
                str(database_path),
            ],
            capture_output=True,
            text=True,
            timeout=CHILD_TIMEOUT_SECONDS,
            env=_child_environment(),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _run_parent() -> int:
    with tempfile.TemporaryDirectory(
        prefix="luxiom_sprint34_interactive_demo_"
    ) as temporary:
        root = Path(temporary).resolve()
        repository = _repository_root().resolve()
        if root == repository or repository in root.parents:
            return 1
        databases = {
            "durability-write": root / "durability.sqlite3",
            "durability-read": root / "durability.sqlite3",
            "membership-denial": root / "membership-denial.sqlite3",
            "permission-denial": root / "permission-denial.sqlite3",
        }
        for phase in PHASES:
            if not _run_child(phase, databases[phase]):
                return 1

    print("DURABILITY WRITE HTTP: PASS")
    print("DURABILITY READ HTTP: PASS")
    print("DURABILITY ITEMS: alpha, beta")
    print("MEMBERSHIP DENIAL HTTP: PASS")
    print("PERMISSION DENIAL HTTP: PASS")
    print("SPRINT 34 LOCAL INTERACTIVE OPERATIONAL PROOF: PASS")
    return 0


def _run_internal(phase: str, raw_path: str) -> int:
    try:
        database_path = validate_demo_database(raw_path, _repository_root())
        if phase == "durability-write":
            run_durability_write(database_path)
        elif phase == "durability-read":
            _, items = run_durability_read_and_observe(database_path)
            if items != ("alpha", "beta"):
                return 1
        elif phase == "membership-denial":
            run_membership_denial(database_path)
        elif phase == "permission-denial":
            run_permission_denial(database_path)
        else:
            return 1
    except (DemoOperationalError, OSError, RuntimeError, ValueError):
        return 1
    return 0


def main(arguments: list[str] | None = None) -> int:
    args = sys.argv[1:] if arguments is None else arguments
    if not args:
        return _run_parent()
    if len(args) == 3 and args[0] == "--internal-phase":
        return _run_internal(args[1], args[2])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
