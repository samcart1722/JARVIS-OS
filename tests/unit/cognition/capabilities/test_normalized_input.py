"""Tests for the deterministic normalized-input capability."""

from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.planning.plan_step import PlanStep


def test_capability_returns_normalized_context_input() -> None:
    result = NormalizedInputCapability().execute(
        CognitiveContext(raw_input="  Raw  ", normalized_input="Normalized"),
        PlanStep(
            id="step-1",
            description="Expose normalized input",
            capability_id="normalized_input",
        ),
    )

    assert result.success is True
    assert result.outputs == ("Normalized",)
    assert result.errors == ()
