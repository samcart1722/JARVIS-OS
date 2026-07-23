"""
Integration tests for Cognitive Memory Engine container registration.
"""

from __future__ import annotations

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
from app.core.container import Container


class TestContainerMemoryPipeline:
    """Tests for Cognitive Memory Pipeline container registration."""

    def test_exposes_default_memory_pipeline(self) -> None:
        container = Container()

        assert isinstance(container.memory_pipeline, DefaultMemoryPipeline)

    def test_initializes_memory_pipeline_collaborators(self) -> None:
        container = Container()

        assert isinstance(container._memory_extractor, DefaultExtractor)
        assert isinstance(container._memory_validator, DefaultValidator)
        assert isinstance(container._memory_classifier, DefaultClassifier)
        assert isinstance(container._memory_repository, InMemoryRepository)
        assert isinstance(container._memory_retriever, DefaultRetriever)
        assert isinstance(container._memory_ranker, DefaultRanker)
        assert container.memory_pipeline._repository is container._memory_repository
        assert container.memory_pipeline._extractor is container._memory_extractor
        assert container.memory_pipeline._validator is container._memory_validator
        assert container.memory_pipeline._classifier is container._memory_classifier
        assert container.memory_pipeline._retriever is container._memory_retriever
        assert container.memory_pipeline._ranker is container._memory_ranker

    def test_reuses_memory_pipeline_singleton_within_container(self) -> None:
        container = Container()

        assert container.memory_pipeline is container.memory_pipeline
