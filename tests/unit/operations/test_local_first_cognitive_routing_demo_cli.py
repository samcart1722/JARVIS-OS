from unittest.mock import patch

from scripts import demo_local_first_cognitive_routing as demo


def test_cli_reports_three_routes_and_zero_remote_calls(capsys) -> None:
    with (
        patch("app.models.ollama_client.OllamaClient.chat") as model,
        patch("app.models.ollama_readiness_probe.OllamaReadinessProbe.check") as ready,
        patch("requests.get") as network_get,
        patch("requests.post") as network_post,
    ):
        assert demo.main() == 0
    output = capsys.readouterr().out
    assert output.count("Scenario ") == 3
    assert "Route: local" in output
    assert "Route: safe_insufficiency" in output
    assert "Route: cognitive" in output
    assert output.count("Cognitive calls: 0") == 2
    assert output.count("Cognitive calls: 1") == 1
    assert "Model calls: 0" in output
    assert "External calls: 0" in output
    assert "Readiness calls: 0" in output
    assert "Network calls: 0" in output
    model.assert_not_called()
    ready.assert_not_called()
    network_get.assert_not_called()
    network_post.assert_not_called()


def test_cli_failure_is_safe(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        demo,
        "Container",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("private")),
    )
    assert demo.main() == 1
    output = capsys.readouterr().out
    assert "failed safely" in output
    assert "private" not in output and "Traceback" not in output
