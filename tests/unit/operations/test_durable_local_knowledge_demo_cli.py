import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import demo_durable_local_knowledge as demo

ROOT = Path(__file__).parents[3]


def test_seed_and_verify_are_separate_processes(tmp_path) -> None:
    database = tmp_path / "cross-process.sqlite3"
    environment = os.environ.copy()
    environment["DEBUG"] = "true"
    command = [
        sys.executable,
        "-m",
        "scripts.demo_durable_local_knowledge",
    ]
    seed = subprocess.run(
        [*command, "seed", "--database", str(database)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    verify = subprocess.run(
        [*command, "verify", "--database", str(database)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert seed.returncode == verify.returncode == 0
    assert "Phase: seed complete" in seed.stdout
    assert "Durable state: seeded" in seed.stdout
    assert "Workspace isolation: verified" not in seed.stdout
    assert "Denied access and mutation: verified" not in seed.stdout
    assert "Phase: verify complete" in verify.stdout
    assert "Workspace isolation: verified" in verify.stdout
    assert "Denied access and mutation: verified" in verify.stdout
    assert "diapers, Gerber, grapes, milk" in verify.stdout
    assert "Model calls: 0" in verify.stdout
    assert "Readiness calls: 0" in verify.stdout
    assert "Network calls: 0" in verify.stdout


@pytest.mark.parametrize("argv", ((), ("seed",), ("bad", "--database", "x")))
def test_invalid_arguments_exit_two(argv) -> None:
    with pytest.raises(SystemExit) as error:
        demo.main(argv)
    assert error.value.code == 2


def test_runtime_failure_is_safe(tmp_path, capsys) -> None:
    code = demo.main(("verify", "--database", str(tmp_path / "missing.sqlite3")))
    output = capsys.readouterr().out
    assert code == 1
    assert "failed safely" in output
    assert "Traceback" not in output and str(tmp_path) not in output
