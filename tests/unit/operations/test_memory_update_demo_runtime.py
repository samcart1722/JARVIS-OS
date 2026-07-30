"""Tests for the explicit scoped memory update demo runtime and report."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
)
from app.cognition.memory.scoped.models import MemoryScope
from app.operations.memory_update_demo_runtime import (
    MEMORY_UPDATE_COMPLETED,
    MEMORY_UPDATE_READINESS_FAILED,
    ExplicitMemoryUpdateDemoReport,
    ExplicitMemoryUpdateDemoRuntime,
)
from app.operations.provider_readiness import (
    PROVIDER_UNAVAILABLE,
    READY,
    ProviderReadinessProbe,
    readiness_result,
)


def success(text: str) -> CognitiveOutcome:
    return CognitiveOutcome(success=True, response=text)


def test_report_is_immutable_and_stores_no_scope() -> None:
    report = ExplicitMemoryUpdateDemoReport(
        status=MEMORY_UPDATE_COMPLETED,
        message="complete",
        readiness=readiness_result(READY),
        before_outcome=success("before"),
        after_outcome=success("after"),
        records_requested=2,
        records_written=2,
        explicit_scope=True,
    )

    assert "memory_scope" not in report.__dataclass_fields__
    assert "contents" not in report.__dataclass_fields__
    with pytest.raises(FrozenInstanceError):
        report.records_written = 0


def test_unready_report_requires_zero_writes_and_no_outcomes() -> None:
    valid = ExplicitMemoryUpdateDemoReport(
        status=MEMORY_UPDATE_READINESS_FAILED,
        message="safe",
        readiness=readiness_result(PROVIDER_UNAVAILABLE),
        before_outcome=None,
        after_outcome=None,
        records_requested=2,
        records_written=0,
        explicit_scope=True,
    )

    assert valid.records_written == 0
    with pytest.raises(ValueError):
        ExplicitMemoryUpdateDemoReport(
            status=MEMORY_UPDATE_READINESS_FAILED,
            message="invalid",
            readiness=readiness_result(PROVIDER_UNAVAILABLE),
            before_outcome=success("unexpected"),
            after_outcome=None,
            records_requested=2,
            records_written=1,
            explicit_scope=True,
        )


def test_completed_report_requires_matching_count_and_both_outcomes() -> None:
    with pytest.raises(ValueError, match="both outcomes"):
        ExplicitMemoryUpdateDemoReport(
            status=MEMORY_UPDATE_COMPLETED,
            message="invalid",
            readiness=readiness_result(READY),
            before_outcome=success("before"),
            after_outcome=None,
            records_requested=2,
            records_written=2,
            explicit_scope=True,
        )
    with pytest.raises(ValueError, match="every requested"):
        ExplicitMemoryUpdateDemoReport(
            status=MEMORY_UPDATE_COMPLETED,
            message="invalid",
            readiness=readiness_result(READY),
            before_outcome=success("before"),
            after_outcome=success("after"),
            records_requested=2,
            records_written=1,
            explicit_scope=True,
        )


def test_report_preserves_structured_cognitive_failures() -> None:
    failure = CognitiveOutcome(
        success=False,
        error=cognitive_error(CAPABILITY_EXECUTION_FAILED),
    )

    report = ExplicitMemoryUpdateDemoReport(
        status=MEMORY_UPDATE_COMPLETED,
        message="complete",
        readiness=readiness_result(READY),
        before_outcome=failure,
        after_outcome=failure,
        records_requested=1,
        records_written=1,
        explicit_scope=True,
    )

    assert report.readiness.ready is True
    assert report.before_outcome is failure
    assert report.after_outcome is failure


def test_runtime_construction_has_no_effects() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    engine = Mock(spec=CognitiveEngine)
    service = Mock(spec=ExplicitMemoryUpdateService)

    ExplicitMemoryUpdateDemoRuntime(
        readiness_probe=probe,
        cognitive_engine=engine,
        update_service=service,
        memory_scope=MemoryScope("scope-a"),
        contents=("one",),
    )

    probe.check.assert_not_called()
    engine.process.assert_not_called()
    service.remember.assert_not_called()


def test_unready_runtime_checks_once_and_stops_without_execution_or_write() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(PROVIDER_UNAVAILABLE)
    engine = Mock(spec=CognitiveEngine)
    service = Mock(spec=ExplicitMemoryUpdateService)

    report = ExplicitMemoryUpdateDemoRuntime(
        readiness_probe=probe,
        cognitive_engine=engine,
        update_service=service,
        memory_scope=MemoryScope("scope-a"),
        contents=("one", "two"),
    ).run("Exact prompt")

    assert report.status == MEMORY_UPDATE_READINESS_FAILED
    assert report.records_requested == 2
    assert report.records_written == 0
    probe.check.assert_called_once_with()
    engine.process.assert_not_called()
    service.remember.assert_not_called()


def test_ready_runtime_preserves_strict_before_write_after_order() -> None:
    events: list[tuple[str, object]] = []
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.side_effect = lambda: (
        events.append(("readiness", None)) or readiness_result(READY)
    )
    engine = Mock(spec=CognitiveEngine)
    engine.process.side_effect = (
        lambda prompt, **kwargs: (
            events.append(("engine", (prompt, kwargs["memory_scope"])))
            or success(f"response-{len(events)}")
        )
    )
    service = Mock(spec=ExplicitMemoryUpdateService)
    service.remember.side_effect = (
        lambda scope, content: events.append(("write", (scope, content)))
    )
    scope = MemoryScope("scope-a")

    report = ExplicitMemoryUpdateDemoRuntime(
        readiness_probe=probe,
        cognitive_engine=engine,
        update_service=service,
        memory_scope=scope,
        contents=("first", "second"),
    ).run("Exact prompt")

    assert report.status == MEMORY_UPDATE_COMPLETED
    assert report.records_written == 2
    assert events == [
        ("readiness", None),
        ("engine", ("Exact prompt", scope)),
        ("write", (scope, "first")),
        ("write", (scope, "second")),
        ("engine", ("Exact prompt", scope)),
    ]
    probe.check.assert_called_once_with()
    assert engine.process.call_count == 2
    assert service.remember.call_count == 2


def test_write_error_propagates_and_prevents_after() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    probe.check.return_value = readiness_result(READY)
    engine = Mock(spec=CognitiveEngine)
    engine.process.return_value = success("before")
    service = Mock(spec=ExplicitMemoryUpdateService)
    service.remember.side_effect = RuntimeError("write failed")

    runtime = ExplicitMemoryUpdateDemoRuntime(
        readiness_probe=probe,
        cognitive_engine=engine,
        update_service=service,
        memory_scope=MemoryScope("scope-a"),
        contents=("first", "second"),
    )

    with pytest.raises(RuntimeError, match="write failed"):
        runtime.run("Exact prompt")
    engine.process.assert_called_once()
    service.remember.assert_called_once()


def test_empty_prompt_is_rejected_before_readiness() -> None:
    probe = Mock(spec=ProviderReadinessProbe)
    runtime = ExplicitMemoryUpdateDemoRuntime(
        readiness_probe=probe,
        cognitive_engine=Mock(spec=CognitiveEngine),
        update_service=Mock(spec=ExplicitMemoryUpdateService),
        memory_scope=MemoryScope("scope-a"),
        contents=("first",),
    )

    with pytest.raises(ValueError, match="cannot be empty"):
        runtime.run(" ")
    probe.check.assert_not_called()
