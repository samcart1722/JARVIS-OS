"""Integration tests for reasoning within Capability Runtime v1."""

import pytest

from app.cognition.capabilities.ids import REASONING_CAPABILITY_ID
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.capabilities.registry import CapabilityRegistry
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.planning.plan import Plan
from app.cognition.planning.plan_step import PlanStep


class StubProvider:
    def __init__(self, response: str) -> None:
        self.response = response

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        del context
        return ReasoningResult(response=self.response)


class ExplodingProvider:
    def generate(self, context: CognitiveContext) -> ReasoningResult:
        del context
        raise RuntimeError("unexpected provider failure")


def execute_reasoning(provider) -> object:
    registry = CapabilityRegistry()
    registry.register(
        REASONING_CAPABILITY_ID,
        ReasoningCapability(ReasoningStage(provider)),
    )
    executor = CapabilityExecutor(registry)
    return executor.execute(
        CognitiveContext(raw_input="Question", normalized_input="Question"),
        Plan(
            steps=(
                PlanStep(
                    id="reasoning-step",
                    description="Reason about the question",
                    capability_id=REASONING_CAPABILITY_ID,
                ),
            )
        ),
    )


def test_executor_resolves_reasoning_and_aggregates_its_output() -> None:
    result = execute_reasoning(StubProvider("Reasoned answer"))

    assert result.success is True
    assert result.completed_steps == ("Reason about the question",)
    assert result.outputs == ("Reasoned answer",)


def test_empty_reasoning_output_preserves_fail_fast_semantics() -> None:
    result = execute_reasoning(StubProvider(""))

    assert result.success is False
    assert result.completed_steps == ()
    assert result.outputs == ()
    assert result.errors == ("Reasoning provider returned no output.",)


def test_unexpected_reasoning_exception_propagates_from_executor() -> None:
    with pytest.raises(RuntimeError, match="unexpected provider failure"):
        execute_reasoning(ExplodingProvider())
