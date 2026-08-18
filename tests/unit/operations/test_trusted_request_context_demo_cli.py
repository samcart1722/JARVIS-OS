"""CLI proofs for the internal trusted request-context demo."""

from unittest.mock import patch

from scripts.demo_trusted_request_context import main


def test_demo_cli_runs_all_scenarios_with_safe_output(capsys) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "Luxiom Internal Trusted Request-Context Demo v1" in output
    assert output.count("Scenario: ") == 7
    for scenario in (
        "valid-permitted",
        "unknown-binding",
        "unknown-workspace",
        "known-unbound-workspace",
        "explicit-second-workspace",
        "downstream-permission-denial",
        "payload-workspace-override",
    ):
        assert f"Scenario: {scenario}" in output
    assert output.count("Status: PASS") == 7
    assert "Router calls: 0" in output
    assert "Model calls: 0" in output
    assert "Provider calls: 0" in output
    assert "Readiness calls: 0" in output
    assert "Network calls: 0" in output
    assert "Overall: PASS" in output
    assert "membership_not_found" not in output
    assert "membership_inactive" not in output
    assert "membership_resolution_failed" not in output
    assert "configured-host-demo-selector" not in output
    assert "Traceback" not in output


def test_demo_cli_failure_is_safe_and_nonzero(capsys) -> None:
    with patch(
        "scripts.demo_trusted_request_context.TrustedRequestContextDemoRuntime.run",
        side_effect=RuntimeError("configured-host-demo-selector sensitive detail"),
    ):
        assert main() == 1
    output = capsys.readouterr().out
    assert "Trusted request-context demo failed safely." in output
    assert "configured-host-demo-selector" not in output
    assert "sensitive detail" not in output
    assert "Traceback" not in output
