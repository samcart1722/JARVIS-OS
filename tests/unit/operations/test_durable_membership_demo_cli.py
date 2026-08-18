"""CLI proofs for the durable membership demo."""

import os
import subprocess
import sys
from pathlib import Path

from scripts.demo_durable_membership import main

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", "scripts/demo_durable_membership.py", *arguments],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_seed_and_verify_succeed_in_separate_processes(tmp_path) -> None:
    path = tmp_path / "membership.sqlite3"
    seeded = _run("seed", "--database", str(path))
    verified = _run("verify", "--database", str(path))
    assert seeded.returncode == 0
    assert "Phase: seed complete" in seeded.stdout
    assert "Overall: PASS" in seeded.stdout
    assert verified.returncode == 0
    assert verified.stdout.count("Status: PASS") == 6
    for status in (
        "local_success",
        "membership_not_found",
        "membership_inactive",
        "local_permission_denied",
        "invalid_knowledge_fields",
    ):
        assert f"Result: {status}" in verified.stdout
    assert "Overall: PASS" in verified.stdout
    assert "calls: 0" in verified.stdout
    assert "Traceback" not in seeded.stderr + verified.stderr


def test_cli_invalid_arguments_and_missing_database_fail_safely(
    tmp_path, capsys
) -> None:
    missing = main(("verify", "--database", str(tmp_path / "missing" / "db.sqlite3")))
    output = capsys.readouterr().out
    assert missing == 1
    assert "failed safely" in output
    process = _run("invalid", "--database", str(tmp_path / "invalid.sqlite3"))
    assert process.returncode != 0
    assert "Traceback" not in process.stderr
    assert "SELECT " not in output + process.stdout + process.stderr
