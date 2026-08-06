"""CLI proof for the Sprint 26 discovery demo."""

from scripts.demo_local_knowledge_discovery import main


def test_demo_cli_exits_zero_and_reports_boundaries(capsys) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "Luxiom Deterministic Local Knowledge Discovery Demo v1" in output
    assert output.count("Scenario ") == 10
    assert "Store calls: 2" in output
    assert "Read calls: 0" in output
    assert "Find calls: 4" in output
    assert "Total repository operations: 6" in output
    assert "Cognitive calls: 1" in output
    assert "Model calls: 0" in output
    assert "External calls: 0" in output
    assert "Readiness calls: 0" in output
    assert "Network calls: 0" in output
