"""
Default implementation of the Cognitive Memory Pipeline.

This module contains the orchestration layer responsible for coordinating
memory extraction, validation, classification, persistence, retrieval,
and ranking.
"""

from __future__ import annotations

from app.cognition.memory.contracts import (
    MemoryClassifier,
    MemoryExtractor,
    MemoryPipeline,
    MemoryRanker,
    MemoryRepository,
    MemoryRetriever,
    MemoryValidator,
)
from app.cognition.memory.domain.entities import (
    MemoryFact,
    MemoryQuery,
    MemoryResult,
    RetrievedMemory,
)
from app.cognition.memory.domain.value_objects import MemoryId


class DefaultMemoryPipeline(MemoryPipeline):
    """
    Default implementation of MemoryPipeline.

    The pipeline coordinates the Cognitive Memory Engine.

    This pipeline delegates extraction, validation, classification,
    persistence, retrieval, and ranking to its collaborators. Invalid
    memories are ignored so only validated memories reach persistence.
    """

    def __init__(
        self,
        repository: MemoryRepository,
        extractor: MemoryExtractor,
        validator: MemoryValidator,
        classifier: MemoryClassifier,
        retriever: MemoryRetriever,
        ranker: MemoryRanker,
    ) -> None:
        self._repository = repository
        self._extractor = extractor
        self._validator = validator
        self._classifier = classifier
        self._retriever = retriever
        self._ranker = ranker

    async def remember(
        self,
        content: str,
    ) -> tuple[MemoryFact, ...]:
        """
        Extract, validate, classify, and persist memories from content.

        Invalid memories are intentionally excluded before classification
        and persistence.
        """
        memories = await self._create_memories(content)
        valid_memories = await self._validate_memories(memories)
        classified_memories = await self._classify_memories(valid_memories)

        return await self._persist_memories(classified_memories)

    async def recall(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """
        Retrieve, transform, and rank memories for a query.

        Repository retrieval metadata is preserved in the returned result.
        """
        result = await self._repository.search(query)
        retrieved_memories = await self._retrieve_memories(
            query,
            result.memories,
        )
        ranked_memories = await self._rank_memories(query, retrieved_memories)

        return self._build_result(result, ranked_memories)

    async def get(
        self,
        memory_id: MemoryId,
    ) -> MemoryFact | None:
        """Retrieve a memory by its identifier."""
        return await self._repository.get(memory_id)

    async def forget(
        self,
        memory_id: MemoryId,
    ) -> None:
        """Remove a memory from persistent storage."""
        await self._repository.delete(memory_id)

    async def _create_memories(
        self,
        content: str,
    ) -> tuple[MemoryFact, ...]:
        """Extract memory facts from raw content."""
        return await self._extractor.extract(content)

    async def _validate_memories(
        self,
        memories: tuple[MemoryFact, ...],
    ) -> tuple[MemoryFact, ...]:
        """Return only memories accepted by the validator."""
        valid_memories: list[MemoryFact] = []

        for memory in memories:
            if await self._validator.validate(memory):
                valid_memories.append(memory)

        return tuple(valid_memories)

    async def _classify_memories(
        self,
        memories: tuple[MemoryFact, ...],
    ) -> tuple[MemoryFact, ...]:
        """Classify each validated memory."""
        classified_memories: list[MemoryFact] = []

        for memory in memories:
            classified_memory = await self._classifier.classify(memory)
            classified_memories.append(classified_memory)

        return tuple(classified_memories)

    async def _persist_memories(
        self,
        memories: tuple[MemoryFact, ...],
    ) -> tuple[MemoryFact, ...]:
        """Persist memories and return those saved successfully."""
        persisted_memories: list[MemoryFact] = []

        for memory in memories:
            await self._repository.save(memory)
            persisted_memories.append(memory)

        return tuple(persisted_memories)

    async def _retrieve_memories(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """Transform or filter memories returned by the repository."""
        return await self._retriever.retrieve(query, memories)

    async def _rank_memories(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """Order memories already retrieved for the query."""
        return await self._ranker.rank(query, memories)

    def _build_result(
        self,
        original: MemoryResult,
        memories: tuple[RetrievedMemory, ...],
    ) -> MemoryResult:
        """Create a result preserving repository metadata and query data."""
        return MemoryResult(
            query=original.query,
            memories=memories,
            execution_time_ms=original.execution_time_ms,
            truncated=original.truncated,
            metadata=original.metadata,
        )
