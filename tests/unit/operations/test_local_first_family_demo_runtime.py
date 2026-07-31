from dataclasses import FrozenInstanceError

import pytest

from app.operations.local_first_family_demo_runtime import (
    LocalFirstFamilyDemoReport,
    create_local_first_family_demo_runtime,
)


def test_exact_demo_scenario_is_local_explicit_and_immutable() -> None:
    report = create_local_first_family_demo_runtime("wife", "family-home").run()
    assert report.initial_add.added == ("diapers", "Gerber", "grapes")
    assert report.initial_read.items == ("diapers", "Gerber", "grapes")
    assert report.duplicate_add.already_present == ("GRAPES",)
    assert report.duplicate_add.added == ("milk",)
    assert report.final_read.items == ("diapers", "Gerber", "grapes", "milk")
    assert not report.denied_read.success and report.denied_read.items == ()
    assert report.denied_list_unchanged
    assert report.actor_explicit and report.workspace_explicit
    assert report.model_calls == report.external_calls == 0
    with pytest.raises(FrozenInstanceError):
        report.status = "changed"


def test_report_rejects_non_local_call_counts() -> None:
    report = create_local_first_family_demo_runtime("a", "w").run()
    values = {field: getattr(report, field) for field in report.__dataclass_fields__}
    values["model_calls"] = 1
    with pytest.raises(ValueError):
        LocalFirstFamilyDemoReport(**values)
