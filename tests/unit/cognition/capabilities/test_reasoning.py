"""Tests for provider-backed ReasoningCapability."""

import pytest

from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import (
    EMPTY_CAPABILITY_OUTPUT,
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
)
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.planning.plan_step import PlanStep


class FakeReasoningProvider:
    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[CognitiveContext] = []

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        self.calls.append(context)
        return ReasoningResult(response=self._response)


class ExplodingReasoningProvider:
    def generate(self, context: CognitiveContext) -> ReasoningResult:
        del context
        raise RuntimeError("provider internal detail")


def context() -> CognitiveContext:
    return CognitiveContext(
        raw_input="Raw request",
        normalized_input="Normalized request",
        permissions=("reason",),
    )


def reasoning_step() -> PlanStep:
    return PlanStep(
        id="reasoning-step",
        description="Reason about the request",
        capability_id="reasoning",
    )


def test_reasoning_capability_invokes_provider_once_and_returns_real_text() -> None:
    provider = FakeReasoningProvider("Provider reasoning output")
    capability = ReasoningCapability(ReasoningStage(provider))
    original_context = context()

    result = capability.execute(original_context, reasoning_step())

    assert result.success is True
    assert result.outputs == ("Provider reasoning output",)
    assert provider.calls == [original_context]
    assert original_context == context()


@pytest.mark.parametrize("empty_response", ["", "   \n"])
def test_reasoning_capability_rejects_empty_output(
    empty_response: str,
) -> None:
    capability = ReasoningCapability(
        ReasoningStage(FakeReasoningProvider(empty_response))
    )

    result = capability.execute(context(), reasoning_step())

    assert result.success is False
    assert result.outputs == ()
    assert result.errors == ("Reasoning provider returned no output.",)
    assert result.error_code == EMPTY_CAPABILITY_OUTPUT


def test_reasoning_capability_propagates_unexpected_provider_exception() -> None:
    capability = ReasoningCapability(
        ReasoningStage(ExplodingReasoningProvider())
    )

    with pytest.raises(RuntimeError, match="provider internal detail"):
        capability.execute(context(), reasoning_step())


def test_reasoning_capability_preserves_controlled_provider_failure() -> None:
    class ControlledFailureProvider:
        def generate(self, context: CognitiveContext) -> ReasoningResult:
            del context
            return ReasoningResult(
                response="",
                error_code=GROUNDED_RESPONSE_PROTOCOL_INVALID,
            )

    result = ReasoningCapability(
        ReasoningStage(ControlledFailureProvider())
    ).execute(context(), reasoning_step())

    assert result.success is False
    assert result.outputs == ()
    assert result.error_code == GROUNDED_RESPONSE_PROTOCOL_INVALID
