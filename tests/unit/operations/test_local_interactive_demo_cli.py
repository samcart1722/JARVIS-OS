import importlib
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _cli():
    return importlib.import_module("scripts.demo_local_interactive")


def test_import_has_no_demo_side_effects(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append((a, k)))

    module = _cli()

    assert callable(module.main)
    assert calls == []


def test_parent_uses_four_bounded_secret_free_child_processes(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    cli = _cli()
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.tempfile, "TemporaryDirectory", _temp_factory(tmp_path))
    monkeypatch.setattr(cli.subprocess, "run", run)

    assert cli.main([]) == 0
    assert len(calls) == 4
    phases = [call[0][3] for call in calls]
    assert phases == list(cli.PHASES)
    durability_paths = [Path(calls[index][0][4]) for index in (0, 1)]
    assert durability_paths[0] == durability_paths[1]
    assert Path(calls[2][0][4]) != durability_paths[0]
    assert Path(calls[3][0][4]) != durability_paths[0]
    for argv, kwargs in calls:
        assert argv[0] == sys.executable
        assert len(argv) == 5
        joined = " ".join(argv).lower()
        assert "proof" not in joined
        assert "csrf" not in joined
        assert kwargs["timeout"] == cli.CHILD_TIMEOUT_SECONDS
        assert demo_secret_names().isdisjoint(kwargs["env"])
    output = capsys.readouterr().out
    assert "SPRINT 34 LOCAL INTERACTIVE OPERATIONAL PROOF: PASS" in output


@pytest.mark.parametrize("failed_index", range(4))
def test_parent_fails_closed_on_each_child_failure(
    tmp_path: Path,
    monkeypatch,
    failed_index: int,
) -> None:
    cli = _cli()
    calls = 0

    def run(argv, **kwargs):
        nonlocal calls
        del argv, kwargs
        result = SimpleNamespace(
            returncode=1 if calls == failed_index else 0,
            stdout="",
            stderr="",
        )
        calls += 1
        return result

    monkeypatch.setattr(cli.tempfile, "TemporaryDirectory", _temp_factory(tmp_path))
    monkeypatch.setattr(cli.subprocess, "run", run)

    assert cli.main([]) == 1
    assert calls == failed_index + 1


def test_internal_arguments_fail_closed(tmp_path: Path) -> None:
    cli = _cli()

    assert cli.main(["--internal-phase"]) == 1
    assert cli.main(["--internal-phase", "unknown", str(tmp_path / "x.db")]) == 1
    assert cli.main(["extra"]) == 1


def test_child_timeout_is_bounded_failure(tmp_path: Path, monkeypatch) -> None:
    cli = _cli()

    def timeout(*args, **kwargs):
        del args, kwargs
        raise subprocess.TimeoutExpired("demo", cli.CHILD_TIMEOUT_SECONDS)

    monkeypatch.setattr(cli.subprocess, "run", timeout)
    assert not cli._run_child("durability-write", tmp_path / "demo.sqlite3")


def test_real_temporary_root_is_cleaned(monkeypatch) -> None:
    cli = _cli()
    roots = []

    def run(argv, **kwargs):
        del kwargs
        roots.append(Path(argv[4]).parent)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.subprocess, "run", run)
    assert cli.main([]) == 0
    assert roots and len(set(roots)) == 1
    assert not roots[0].exists()


def _temp_factory(path: Path):
    class TemporaryDirectory:
        def __init__(self, **kwargs) -> None:
            assert kwargs["prefix"].startswith("luxiom_sprint34")

        def __enter__(self) -> str:
            path.mkdir(exist_ok=True)
            return str(path)

        def __exit__(self, *args) -> None:
            del args

    return TemporaryDirectory


def demo_secret_names() -> set[str]:
    return {"LUXIOM_PROOF", "LUXIOM_CSRF", "AUTH_TOKEN"}
