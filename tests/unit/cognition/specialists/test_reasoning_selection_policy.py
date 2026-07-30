"""Tests for deterministic reasoning-capability selection."""

import pytest

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.specialists.deterministic_reasoning_selection_policy import (
    DeterministicReasoningSelectionPolicy,
)


def context(prompt: str) -> CognitiveContext:
    return CognitiveContext(raw_input=prompt, normalized_input=prompt)


@pytest.mark.parametrize(
    ("enabled", "expected"),
    (
        (False, NORMALIZED_INPUT_CAPABILITY_ID),
        (True, REASONING_CAPABILITY_ID),
    ),
)
def test_policy_selects_only_from_explicit_enablement(
    enabled: bool,
    expected: str,
) -> None:
    policy = DeterministicReasoningSelectionPolicy(enabled)
    original = context("Explain a complex reasoning problem with Ollama")

    first = policy.select_capability(original)
    second = policy.select_capability(original)

    assert first == expected
    assert second == expected
    assert original == context(
        "Explain a complex reasoning problem with Ollama"
    )


@pytest.mark.parametrize(
    "prompt",
    (
        "reason analyze explain",
        "simple complex reasoning Ollama",
        "Completely unrelated input",
    ),
)
def test_prompt_content_never_changes_disabled_selection(prompt: str) -> None:
    policy = DeterministicReasoningSelectionPolicy(False)

    assert (
        policy.select_capability(context(prompt))
        == NORMALIZED_INPUT_CAPABILITY_ID
    )


def test_different_prompts_have_same_enabled_selection() -> None:
    policy = DeterministicReasoningSelectionPolicy(True)

    assert policy.select_capability(context("simple")) == (
        REASONING_CAPABILITY_ID
    )
    assert policy.select_capability(context("complex Ollama reasoning")) == (
        REASONING_CAPABILITY_ID
    )
