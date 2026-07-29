"""Behavioral tests for Capability Runtime v1."""

from collections.abc import Iterable

import pytest

from app.cognition.capabilities.capability import Capability
from app.cognition.capabilities.capability_result import CapabilityResult
from app.cognition.capabilities.registry import CapabilityRegistry
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.planning.plan import Plan
from app.cognition.planning.plan_step import PlanStep


class RecordingCapability(Capability):
    def __init__(self, results: Iterable[CapabilityResult]) -> None:
        self._results = iter(results)
        self.calls: list[tuple[CognitiveContext, PlanStep]] = []

    def execute(
        self,
        context: CognitiveContext,
        step: PlanStep,
    ) -> CapabilityResult:
        self.calls.append((context, step))
        return next(self._results)


class ExplodingCapability(Capability):
    def execute(
        self,
        context: CognitiveContext,
        step: PlanStep,
    ) -> CapabilityResult:
        del context, step
        raise RuntimeError("unexpected internal detail")


def context() -> CognitiveContext:
    return CognitiveContext(raw_input="Raw", normalized_input="Normalized")


def step(step_id: str, capability_id: str = "record") -> PlanStep:
    return PlanStep(
        id=step_id,
        description=f"Step {step_id}",
        capability_id=capability_id,
    )


def executor_with(capability: Capability) -> CapabilityExecutor:
    registry = CapabilityRegistry()
    registry.register("record", capability)
    return CapabilityExecutor(registry)


def test_executor_passes_same_context_and_steps_in_order_and_aggregates() -> None:
    capability = RecordingCapability(
        (
            CapabilityResult(
                success=True,
                outputs=("first output",),
                metadata={"sequence": 1},
            ),
            CapabilityResult(
                success=True,
                outputs=("second output",),
                metadata={"sequence": 2},
            ),
        )
    )
    executor = executor_with(capability)
    request_context = context()
    first = step("1")
    second = step("2")

    result = executor.execute(request_context, Plan(steps=(first, second)))

    assert result.success is True
    assert result.completed_steps == ("Step 1", "Step 2")
    assert result.outputs == ("first output", "second output")
    assert result.metadata == ({"sequence": 1}, {"sequence": 2})
    assert capability.calls == [
        (request_context, first),
        (request_context, second),
    ]


def test_executor_fails_fast_and_preserves_prior_successes() -> None:
    capability = RecordingCapability(
        (
            CapabilityResult(success=True, outputs=("valid output",)),
            CapabilityResult(success=False, errors=("controlled failure",)),
            CapabilityResult(success=True, outputs=("must not run",)),
        )
    )
    executor = executor_with(capability)

    result = executor.execute(
        context(),
        Plan(steps=(step("1"), step("2"), step("3"))),
    )

    assert result.success is False
    assert result.completed_steps == ("Step 1",)
    assert result.outputs == ("valid output",)
    assert result.errors == ("controlled failure",)
    assert len(capability.calls) == 2


def test_executor_returns_failure_when_capability_is_missing() -> None:
    executor = CapabilityExecutor(CapabilityRegistry())

    result = executor.execute(
        context(),
        Plan(steps=(step("1", capability_id="missing"),)),
    )

    assert result.success is False
    assert result.completed_steps == ()
    assert result.outputs == ()
    assert result.errors == ("Capability is not available: missing",)


def test_executor_does_not_share_results_between_executions() -> None:
    capability = RecordingCapability(
        (
            CapabilityResult(success=True, outputs=("first",)),
            CapabilityResult(success=True, outputs=("second",)),
        )
    )
    executor = executor_with(capability)

    first = executor.execute(context(), Plan(steps=(step("1"),)))
    second = executor.execute(context(), Plan(steps=(step("2"),)))

    assert first.completed_steps == ("Step 1",)
    assert first.outputs == ("first",)
    assert second.completed_steps == ("Step 2",)
    assert second.outputs == ("second",)


def test_empty_plan_succeeds_without_completed_work() -> None:
    result = CapabilityExecutor(CapabilityRegistry()).execute(
        context(),
        Plan(steps=()),
    )

    assert result.success is True
    assert result.completed_steps == ()
    assert result.outputs == ()
    assert result.errors == ()


def test_unexpected_capability_exception_propagates() -> None:
    executor = executor_with(ExplodingCapability())

    with pytest.raises(RuntimeError, match="unexpected internal detail"):
        executor.execute(context(), Plan(steps=(step("1"),)))
