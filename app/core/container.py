"""
Application Composition Root.

This module is responsible for constructing and wiring the
application services.

It is intentionally simple and framework-independent.
"""

from __future__ import annotations

from app.cognition.capabilities.ids import (
    NORMALIZED_INPUT_CAPABILITY_ID,
    REASONING_CAPABILITY_ID,
)
from app.cognition.capabilities.normalized_input import NormalizedInputCapability
from app.cognition.capabilities.reasoning import ReasoningCapability
from app.cognition.capabilities.registry import CapabilityRegistry
from app.cognition.classification.default_goal_classifier import (
    DefaultGoalClassifier,
)
from app.cognition.engine import CognitiveEngine
from app.cognition.memory.extractors.default_extractor import DefaultExtractor
from app.cognition.memory.intelligence.default_classifier import (
    DefaultClassifier,
)
from app.cognition.memory.persistence.in_memory_repository import (
    InMemoryRepository,
)
from app.cognition.memory.pipeline.default_memory_pipeline import (
    DefaultMemoryPipeline,
)
from app.cognition.memory.ranking.default_ranker import DefaultRanker
from app.cognition.memory.retrieval.default_retriever import DefaultRetriever
from app.cognition.memory.validation.default_validator import (
    DefaultValidator,
)
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.providers.ollama_provider import OllamaProvider
from app.cognition.specialists.specialist_router import SpecialistRouter
from app.core.compatibility.legacy_memory_adapter import LegacyMemoryAdapter


class Container:
    """
    Central application composition root.

    This class creates and owns long-lived application services.
    """

    def __init__(self) -> None:
        self._build_memory()
        self._build_reasoning()
        self._build_context()
        self._build_prompt()
        self._build_models()
        self._build_reflection()
        self._build_learning()
        self._build_tools()
        self._build_vision()
        self._build_speech()

    def _build_memory(self) -> None:
        """Compose Cognitive Memory Engine services."""
        self._memory_repository = InMemoryRepository()
        self._memory_extractor = DefaultExtractor()
        self._memory_validator = DefaultValidator()
        self._memory_classifier = DefaultClassifier()
        self._memory_retriever = DefaultRetriever()
        self._memory_ranker = DefaultRanker()

        self.memory_pipeline = DefaultMemoryPipeline(
            repository=self._memory_repository,
            extractor=self._memory_extractor,
            validator=self._memory_validator,
            classifier=self._memory_classifier,
            retriever=self._memory_retriever,
            ranker=self._memory_ranker,
        )
        self.memory = LegacyMemoryAdapter(self.memory_pipeline)

    def _build_reasoning(self) -> None:
        """Compose the Cognitive Engine entry point."""
        self.goal_classifier = DefaultGoalClassifier()
        self.specialist_router = SpecialistRouter()
        self.normalized_input_capability = NormalizedInputCapability()
        self.reasoning_provider = OllamaProvider()
        self.reasoning_stage = ReasoningStage(self.reasoning_provider)
        self.reasoning_capability = ReasoningCapability(self.reasoning_stage)
        self.capability_registry = CapabilityRegistry()
        self.capability_registry.register(
            NORMALIZED_INPUT_CAPABILITY_ID,
            self.normalized_input_capability,
        )
        self.capability_registry.register(
            REASONING_CAPABILITY_ID,
            self.reasoning_capability,
        )
        self.capability_executor = CapabilityExecutor(self.capability_registry)
        self.response_stage = ResponseStage()
        self.cognitive_engine = CognitiveEngine(
            goal_classifier=self.goal_classifier,
            specialist_router=self.specialist_router,
            capability_executor=self.capability_executor,
            response_stage=self.response_stage,
        )

    def _build_context(self) -> None:
        """Compose context services."""
        pass

    def _build_prompt(self) -> None:
        """Compose prompt services."""
        pass

    def _build_models(self) -> None:
        """Compose model services."""
        pass

    def _build_reflection(self) -> None:
        """Compose reflection services."""
        pass

    def _build_learning(self) -> None:
        """Compose learning services."""
        pass

    def _build_tools(self) -> None:
        """Compose tool services."""
        pass

    def _build_vision(self) -> None:
        """Compose vision services."""
        pass

    def _build_speech(self) -> None:
        """Compose speech services."""
        pass


container = Container()
