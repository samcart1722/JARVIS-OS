import os

import pytest

from scripts import demo_local_first_family_resolution as demo


@pytest.mark.parametrize(
    "argv", ((), ("--actor-id", "a"), ("--actor-id", " ", "--workspace-id", "w"))
)
def test_invalid_arguments_exit_two(argv) -> None:
    with pytest.raises(SystemExit) as error:
        demo.main(argv)
    assert error.value.code == 2


def test_cli_success_is_safe_offline_and_does_not_mutate_environment(capsys) -> None:
    before = os.environ.copy()
    code = demo.main(("--actor-id", "private-actor", "--workspace-id", "private-space"))
    output = capsys.readouterr().out
    assert code == 0
    assert "Model calls: 0" in output and "External calls: 0" in output
    assert "diapers, Gerber, grapes, milk" in output
    for unsafe in (
        "private-actor",
        "private-space",
        "http://",
        "Traceback",
        "Ollama",
        "{",
    ):
        assert unsafe not in output
    assert os.environ == before


def test_cli_failure_is_safe(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        demo,
        "create_local_first_family_demo_runtime",
        lambda *args: (_ for _ in ()).throw(RuntimeError("secret URL")),
    )
    assert demo.main(("--actor-id", "a", "--workspace-id", "w")) == 1
    output = capsys.readouterr().out
    assert "failed safely" in output and "secret URL" not in output
