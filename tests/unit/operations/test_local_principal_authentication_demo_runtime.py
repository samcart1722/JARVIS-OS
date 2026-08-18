"""Focused proofs for the local-principal authentication demo."""

from dataclasses import fields

import pytest

from app.operations.local_principal_authentication_demo_runtime import (
    LocalPrincipalAuthenticationDemoReport,
    LocalPrincipalAuthenticationScenarioReport,
)
from scripts.demo_local_principal_authentication import _build_report

EXPECTED_IDS = (
    "authenticated-active-permitted",
    "authentication-failure-precedes-invalid-workspace",
    "mapping-failure-precedes-invalid-workspace",
    "workspace-selection-invalid",
    "membership-not-found",
    "membership-inactive",
    "authenticated-active-permission-denied",
    "authenticated-payload-workspace-override-rejected",
)
EXPECTED_STATUSES = (
    "local_success",
    "authentication_failed",
    "principal_mapping_failed",
    "workspace_selection_invalid",
    "membership_not_found",
    "membership_inactive",
    "local_permission_denied",
    "invalid_knowledge_fields",
)
EXPECTED_DELTAS = (
    (1, 1, 1, 1, 1, 1, 0),
    (1, 0, 0, 0, 0, 0, 0),
    (1, 1, 0, 0, 0, 0, 0),
    (1, 1, 0, 0, 0, 0, 0),
    (1, 1, 1, 0, 0, 0, 0),
    (1, 1, 1, 0, 0, 0, 0),
    (1, 1, 1, 1, 1, 0, 0),
    (1, 1, 1, 1, 0, 0, 0),
)


def _deltas(scenario):
    return (
        scenario.authenticator_calls,
        scenario.mapper_calls,
        scenario.membership_calls,
        scenario.router_calls,
        scenario.permission_calls,
        scenario.repository_calls,
        scenario.cognitive_calls,
    )


def test_all_eight_scenarios_prove_exact_results_and_boundaries() -> None:
    report = _build_report()
    assert report.success
    assert tuple(s.scenario_id for s in report.scenarios) == EXPECTED_IDS
    assert tuple(s.status for s in report.scenarios) == EXPECTED_STATUSES
    assert tuple(_deltas(s) for s in report.scenarios) == EXPECTED_DELTAS
    assert all(s.passed for s in report.scenarios)
    assert all(s.cognitive_calls == 0 for s in report.scenarios)
    assert (
        report.model_calls,
        report.provider_calls,
        report.readiness_calls,
        report.network_calls,
    ) == (0, 0, 0, 0)


def test_stage_success_progresses_only_after_each_boundary() -> None:
    scenarios = _build_report().scenarios
    assert scenarios[0].authentication_success
    assert scenarios[0].mapping_success
    assert scenarios[0].workspace_success
    assert scenarios[0].membership_success
    assert not scenarios[1].authentication_success
    assert not scenarios[1].mapping_success
    assert scenarios[2].authentication_success
    assert not scenarios[2].mapping_success
    assert scenarios[3].mapping_success
    assert not scenarios[3].workspace_success
    assert scenarios[4].workspace_success
    assert not scenarios[4].membership_success
    assert scenarios[5].workspace_success
    assert not scenarios[5].membership_success
    assert scenarios[6].membership_success
    assert scenarios[7].membership_success


def test_reports_exclude_proof_and_verifier_material() -> None:
    names = {
        field.name
        for model in (
            LocalPrincipalAuthenticationScenarioReport,
            LocalPrincipalAuthenticationDemoReport,
        )
        for field in fields(model)
    }
    assert "proof" not in names
    assert "verifier" not in names
    assert "verifier_value" not in names


def test_report_requires_exactly_eight_scenarios() -> None:
    report = _build_report()
    with pytest.raises(ValueError, match="requires eight"):
        LocalPrincipalAuthenticationDemoReport(report.scenarios[:-1])


@pytest.mark.parametrize(
    "field_name",
    ("model_calls", "provider_calls", "readiness_calls", "network_calls"),
)
def test_report_rejects_any_remote_or_model_call(field_name: str) -> None:
    report = _build_report()
    values = {field_name: 1}
    with pytest.raises(ValueError, match="cannot use remote calls"):
        LocalPrincipalAuthenticationDemoReport(report.scenarios, **values)


def test_report_success_requires_every_scenario_to_pass() -> None:
    report = _build_report()
    failed = LocalPrincipalAuthenticationScenarioReport(
        **{
            field.name: (
                False
                if field.name == "passed"
                else getattr(report.scenarios[0], field.name)
            )
            for field in fields(LocalPrincipalAuthenticationScenarioReport)
        }
    )
    changed = LocalPrincipalAuthenticationDemoReport(
        (failed, *report.scenarios[1:])
    )
    assert not changed.success
