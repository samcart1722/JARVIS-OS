"""
Application Composition Root.

This module is responsible for constructing and wiring the
application services.

It is intentionally simple and framework-independent.
"""

from __future__ import annotations

from collections.abc import Iterable

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
from app.cognition.memory.scoped.context_retriever import (
    RepositoryMemoryContextRetriever,
)
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
)
from app.cognition.memory.scoped.in_memory_repository import (
    InMemoryScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import ScopedMemoryRecord
from app.cognition.memory.validation.default_validator import (
    DefaultValidator,
)
from app.cognition.pipeline.reasoning_stage import ReasoningStage
from app.cognition.pipeline.response_stage import ResponseStage
from app.cognition.planning.capability_executor import CapabilityExecutor
from app.cognition.prompts.reasoning import MemoryAwareReasoningPromptBuilder
from app.cognition.providers.ollama_provider import OllamaProvider
from app.cognition.specialists.default_specialist import DefaultSpecialist
from app.cognition.specialists.deterministic_reasoning_selection_policy import (
    DeterministicReasoningSelectionPolicy,
)
from app.cognition.specialists.specialist_router import SpecialistRouter
from app.core.compatibility.legacy_memory_adapter import LegacyMemoryAdapter
from app.core.config import Settings, settings
from app.models.ollama_client import OllamaClient
from app.models.ollama_readiness_probe import OllamaReadinessProbe


class Container:
    """
    Central application composition root.

    This class creates and owns long-lived application services.
    """

    def __init__(
        self,
        app_settings: Settings = settings,
        *,
        scoped_memory_records: Iterable[ScopedMemoryRecord] = (),
    ) -> None:
        if isinstance(scoped_memory_records, (str, bytes)):
            raise TypeError("Scoped memory records must be a collection of records.")
        self._settings = app_settings
        self._scoped_memory_records = tuple(scoped_memory_records)
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
        self.scoped_memory_repository = InMemoryScopedMemoryRepository(
            self._scoped_memory_records
        )
        self.memory_context_retriever = RepositoryMemoryContextRetriever(
            self.scoped_memory_repository
        )
        self.explicit_memory_update_service = ExplicitMemoryUpdateService(
            self.scoped_memory_repository,
            enabled=self._settings.MEMORY_UPDATE_ENABLED,
        )

    def _build_reasoning(self) -> None:
        """Compose the Cognitive Engine entry point."""
        self.goal_classifier = DefaultGoalClassifier()
        self.reasoning_selection_policy = (
            DeterministicReasoningSelectionPolicy(
                reasoning_enabled=self._settings.REASONING_ENABLED
            )
        )
        self.default_specialist = DefaultSpecialist(
            self.reasoning_selection_policy
        )
        self.specialist_router = SpecialistRouter(self.default_specialist)
        self.normalized_input_capability = NormalizedInputCapability()
        self.ollama_client = OllamaClient(
            base_url=self._settings.OLLAMA_BASE_URL,
            models_url=self._settings.OLLAMA_MODELS_URL,
            model=self._settings.OLLAMA_MODEL,
            timeout_seconds=self._settings.OLLAMA_TIMEOUT_SECONDS,
        )
        self.provider_readiness_probe = OllamaReadinessProbe(self.ollama_client)
        self.reasoning_prompt_builder = MemoryAwareReasoningPromptBuilder(
            memory_context_enabled=(
                self._settings.MEMORY_PROMPT_CONTEXT_ENABLED
            ),
            max_records=self._settings.MEMORY_PROMPT_MAX_RECORDS,
            max_characters=self._settings.MEMORY_PROMPT_MAX_CHARACTERS,
        )
        self.reasoning_provider = OllamaProvider(
            self.ollama_client,
            self.reasoning_prompt_builder,
        )
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
            memory_context_retriever=self.memory_context_retriever,
            memory_retrieval_enabled=self._settings.MEMORY_RETRIEVAL_ENABLED,
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
