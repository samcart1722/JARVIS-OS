"""Cognitive Engine entry point."""

from __future__ import annotations

from app.cognition.pipeline import (
    ContextStage,
    InputStage,
    ReasoningStage,
    ResponseStage,
)


class CognitiveEngine:
    """Orchestrate the ordered cognitive processing pipeline."""

    def __init__(self, reasoning_stage: ReasoningStage) -> None:
        self._input_stage = InputStage()
        self._context_stage = ContextStage()
        self._reasoning_stage = reasoning_stage
        self._response_stage = ResponseStage()

    def process(self, user_input: str) -> str:
        """Process user input through all cognitive pipeline stages."""
        context = self._input_stage.process(user_input)
        context = self._context_stage.process(context)
        reasoning_result = self._reasoning_stage.process(context)
        return self._response_stage.process(reasoning_result)
