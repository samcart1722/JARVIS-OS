"""
Unit tests for the default Cognitive Memory Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.cognition.memory.domain.entities import (
    MemoryFact,
    MemoryQuery,
    MemoryResult,
    RetrievedMemory,
)
from app.cognition.memory.domain.enums import MemoryCategory, MemorySource
from app.cognition.memory.domain.value_objects import MemoryConfidence, MemoryId
from app.cognition.memory.pipeline.default_memory_pipeline import (
    DefaultMemoryPipeline,
)
from app.tests.cognition.memory.pipeline.fakes import (
    FakeClassifier,
    FakeExtractor,
    FakeMemoryRepository,
    FakeRanker,
    FakeRetriever,
    FakeValidator,
)


@dataclass(slots=True)
class PipelineCollaborators:
    """Collaborators used to exercise a default memory pipeline."""

    pipeline: DefaultMemoryPipeline
    repository: FakeMemoryRepository
    extractor: FakeExtractor
    validator: FakeValidator
    classifier: FakeClassifier
    retriever: FakeRetriever
    ranker: FakeRanker


def _create_memory(
    category: MemoryCategory = MemoryCategory.CONVERSATION,
) -> MemoryFact:
    """Create a memory fact for pipeline orchestration tests."""
    return MemoryFact(
        id=MemoryId(),
        content="Remember this fact.",
        category=category,
        source=MemorySource.USER,
        confidence=MemoryConfidence(1.0),
    )


def _create_query(
    text: str = "Default query",
) -> MemoryQuery:
    """Create a memory query for pipeline orchestration tests."""
    return MemoryQuery(text=text)


def _create_pipeline(
    memories: tuple[MemoryFact, ...] = (),
) -> PipelineCollaborators:
    """Create a pipeline with deterministic in-memory collaborators."""
    repository = FakeMemoryRepository()
    extractor = FakeExtractor(memories)
    validator = FakeValidator()
    classifier = FakeClassifier()
    retriever = FakeRetriever()
    ranker = FakeRanker()
    pipeline = DefaultMemoryPipeline(
        repository=repository,
        extractor=extractor,
        validator=validator,
        classifier=classifier,
        retriever=retriever,
        ranker=ranker,
    )

    return PipelineCollaborators(
        pipeline=pipeline,
        repository=repository,
        extractor=extractor,
        validator=validator,
        classifier=classifier,
        retriever=retriever,
        ranker=ranker,
    )


async def _store(
    collaborators: PipelineCollaborators,
    *memories: MemoryFact,
) -> None:
    """Store memory facts in the fake repository."""
    for memory in memories:
        await collaborators.repository.save(memory)


class TestRemember:
    """Tests for memory creation orchestration."""

    @pytest.mark.asyncio
    async def test_extracts_memories(self) -> None:
        collaborators = _create_pipeline()

        await collaborators.pipeline.remember("A memory to extract.")

        assert collaborators.extractor.calls == 1
        assert collaborators.extractor.contents == ["A memory to extract."]

    @pytest.mark.asyncio
    async def test_validates_all_memories(self) -> None:
        first_memory = _create_memory()
        second_memory = _create_memory()
        collaborators = _create_pipeline((first_memory, second_memory))

        await collaborators.pipeline.remember("Memories to validate.")

        assert collaborators.validator.validated == [
            first_memory.id,
            second_memory.id,
        ]

    @pytest.mark.asyncio
    async def test_discards_invalid_memories(self) -> None:
        valid_memory = _create_memory()
        invalid_memory = _create_memory()
        collaborators = _create_pipeline((valid_memory, invalid_memory))
        collaborators.validator.invalid_ids.add(invalid_memory.id)

        await collaborators.pipeline.remember("Memories with one invalid fact.")

        assert collaborators.repository.saved == [valid_memory]

    @pytest.mark.asyncio
    async def test_classifies_valid_memories(self) -> None:
        memory = _create_memory()
        collaborators = _create_pipeline((memory,))
        collaborators.classifier.classification_overrides[memory.id] = (
            MemoryCategory.PROJECT
        )

        await collaborators.pipeline.remember("A memory to classify.")

        assert collaborators.classifier.classified == [memory.id]
        assert collaborators.repository.saved[0].category is MemoryCategory.PROJECT

    @pytest.mark.asyncio
    async def test_persists_only_valid_memories(self) -> None:
        valid_memory = _create_memory()
        invalid_memory = _create_memory()
        collaborators = _create_pipeline((valid_memory, invalid_memory))
        collaborators.validator.invalid_ids.add(invalid_memory.id)

        await collaborators.pipeline.remember("Memories to persist.")

        assert collaborators.repository.saved == [valid_memory]

    @pytest.mark.asyncio
    async def test_returns_only_persisted_memories(self) -> None:
        valid_memory = _create_memory()
        invalid_memory = _create_memory()
        collaborators = _create_pipeline((valid_memory, invalid_memory))
        collaborators.validator.invalid_ids.add(invalid_memory.id)

        persisted_memories = await collaborators.pipeline.remember(
            "Memories to return."
        )

        assert persisted_memories == (valid_memory,)
        assert persisted_memories == tuple(collaborators.repository.saved)


class TestRecall:
    """Tests for memory retrieval orchestration."""

    @pytest.mark.asyncio
    async def test_searches_repository(self) -> None:
        memory = _create_memory()
        collaborators = _create_pipeline()
        await _store(collaborators, memory)
        query = _create_query("Find the memory.")

        await collaborators.pipeline.recall(query)

        assert collaborators.repository.search_queries == [query]

    @pytest.mark.asyncio
    async def test_calls_retriever(self) -> None:
        memory = _create_memory()
        collaborators = _create_pipeline()
        await _store(collaborators, memory)
        query = _create_query("Retrieve the memory.")

        await collaborators.pipeline.recall(query)

        assert collaborators.retriever.calls == 1
        assert collaborators.retriever.last_query is query
        assert collaborators.retriever.last_memories is not None
        assert tuple(
            retrieved.memory
            for retrieved in collaborators.retriever.last_memories
        ) == (memory,)

    @pytest.mark.asyncio
    async def test_calls_ranker(self) -> None:
        memory = _create_memory()
        transformed_memories = (
            RetrievedMemory(memory=memory, relevance_score=0.8),
        )
        collaborators = _create_pipeline()
        collaborators.retriever.result_override = transformed_memories
        query = _create_query("Rank the memory.")

        await collaborators.pipeline.recall(query)

        assert collaborators.ranker.calls == 1
        assert collaborators.ranker.last_query is query
        assert collaborators.ranker.last_memories is not None
        assert tuple(
            retrieved.memory
            for retrieved in collaborators.ranker.last_memories
        ) == (memory,)

    @pytest.mark.asyncio
    async def test_preserves_repository_metadata(self) -> None:
        collaborators = _create_pipeline()
        query = _create_query("Preserve result metadata.")

        result: MemoryResult = await collaborators.pipeline.recall(query)

        assert result.query is query
        assert result.execution_time_ms == 0
        assert result.truncated is False
        assert result.metadata == {}

    @pytest.mark.asyncio
    async def test_returns_new_memory_result(self) -> None:
        memory = _create_memory()
        ranked_memories = (
            RetrievedMemory(memory=memory, relevance_score=0.9),
        )
        collaborators = _create_pipeline()
        collaborators.ranker.result_override = ranked_memories
        query = _create_query("Return ranked memories.")
        original_result = await collaborators.repository.search(query)

        result = await collaborators.pipeline.recall(query)

        assert result is not original_result
        assert result.memories is ranked_memories


class TestGet:
    """Tests for memory lookup orchestration."""

    @pytest.mark.asyncio
    async def test_get_delegates_to_repository(self) -> None:
        memory = _create_memory()
        collaborators = _create_pipeline()
        await _store(collaborators, memory)

        result = await collaborators.pipeline.get(memory.id)

        assert collaborators.repository.loaded == [memory.id]
        assert result is memory


class TestForget:
    """Tests for memory deletion orchestration."""

    @pytest.mark.asyncio
    async def test_forget_delegates_to_repository(self) -> None:
        memory = _create_memory()
        collaborators = _create_pipeline()
        await _store(collaborators, memory)

        await collaborators.pipeline.forget(memory.id)

        assert collaborators.repository.deleted == [memory.id]
        assert await collaborators.repository.get(memory.id) is None
