"""
Reusable fake implementations for Cognitive Memory Engine tests.
"""

from __future__ import annotations

from dataclasses import replace

from app.cognition.memory.contracts import (
    MemoryClassifier,
    MemoryExtractor,
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
from app.cognition.memory.domain.enums import MemoryCategory
from app.cognition.memory.domain.value_objects import MemoryId


class FakeMemoryRepository(MemoryRepository):
    """In-memory repository fake exposing state for unit test assertions."""

    def __init__(self) -> None:
        self._storage: dict[MemoryId, MemoryFact] = {}
        self.saved: list[MemoryFact] = []
        self.deleted: list[MemoryId] = []
        self.loaded: list[MemoryId] = []
        self.search_queries: list[MemoryQuery] = []

    async def save(
        self,
        memory: MemoryFact,
    ) -> None:
        """Store a memory and record the save operation."""
        self._storage[memory.id] = memory
        self.saved.append(memory)

    async def get(
        self,
        memory_id: MemoryId,
    ) -> MemoryFact | None:
        """Return the stored memory for an identifier, if present."""
        self.loaded.append(memory_id)
        return self._storage.get(memory_id)

    async def delete(
        self,
        memory_id: MemoryId,
    ) -> None:
        """Remove a memory when present and record the deletion."""
        self._storage.pop(memory_id, None)
        self.deleted.append(memory_id)

    async def exists(
        self,
        memory_id: MemoryId,
    ) -> bool:
        """Return whether a memory is stored for an identifier."""
        return memory_id in self._storage

    async def search(
        self,
        query: MemoryQuery,
    ) -> MemoryResult:
        """Return all stored memories as deterministic retrieved memories."""
        self.search_queries.append(query)
        memories = tuple(
            RetrievedMemory(
                memory=memory,
                relevance_score=1.0,
            )
            for memory in self._storage.values()
        )

        return MemoryResult(
            query=query,
            memories=memories,
            execution_time_ms=0,
            truncated=False,
            metadata={},
        )

    def reset(self) -> None:
        """Clear recorded state and in-memory storage."""
        self._storage.clear()
        self.saved.clear()
        self.deleted.clear()
        self.loaded.clear()
        self.search_queries.clear()


class FakeExtractor(MemoryExtractor):
    """Extractor fake exposing invocations for unit test assertions."""

    def __init__(
        self,
        memories: tuple[MemoryFact, ...] = (),
    ) -> None:
        self.memories = memories
        self.calls = 0
        self.contents: list[str] = []

    async def extract(
        self,
        content: str,
    ) -> tuple[MemoryFact, ...]:
        """Return the configured memory facts."""
        self.calls += 1
        self.contents.append(content)
        return self.memories

    def reset(self) -> None:
        """Clear recorded invocation state."""
        self.calls = 0
        self.contents.clear()


class FakeValidator(MemoryValidator):
    """Validator fake exposing validations for unit test assertions."""

    def __init__(
        self,
        invalid_ids: set[MemoryId] | None = None,
    ) -> None:
        self.invalid_ids = invalid_ids if invalid_ids is not None else set()
        self.validated: list[MemoryId] = []

    async def validate(
        self,
        memory: MemoryFact,
    ) -> bool:
        """Record validation and accept memories not marked invalid."""
        self.validated.append(memory.id)
        return memory.id not in self.invalid_ids

    def reset(self) -> None:
        """Clear recorded validation state."""
        self.validated.clear()


class FakeClassifier(MemoryClassifier):
    """Classifier fake exposing classifications for unit test assertions."""

    def __init__(
        self,
        classification_overrides: dict[MemoryId, MemoryCategory] | None = None,
    ) -> None:
        self.classified: list[MemoryId] = []
        self.classification_overrides = (
            classification_overrides
            if classification_overrides is not None
            else {}
        )

    async def classify(
        self,
        memory: MemoryFact,
    ) -> MemoryFact:
        """Record classification and return an overridden copy when needed."""
        self.classified.append(memory.id)
        category = self.classification_overrides.get(memory.id)

        if category is None:
            return memory

        return replace(memory, category=category)

    def reset(self) -> None:
        """Clear recorded classification state."""
        self.classified.clear()


class FakeRetriever(MemoryRetriever):
    """Retriever fake exposing calls for unit test assertions."""

    def __init__(
        self,
        result_override: tuple[RetrievedMemory, ...] | None = None,
    ) -> None:
        self.calls = 0
        self.last_query: MemoryQuery | None = None
        self.last_memories: tuple[RetrievedMemory, ...] | None = None
        self.result_override = result_override

    async def retrieve(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """Record retrieval inputs and return the configured result if present."""
        self.calls += 1
        self.last_query = query
        self.last_memories = memories

        if self.result_override is not None:
            return self.result_override

        return memories

    def reset(self) -> None:
        """Clear recorded retrieval state."""
        self.calls = 0
        self.last_query = None
        self.last_memories = None


class FakeRanker(MemoryRanker):
    """Ranker fake exposing calls for unit test assertions."""

    def __init__(
        self,
        result_override: tuple[RetrievedMemory, ...] | None = None,
    ) -> None:
        self.calls = 0
        self.last_query: MemoryQuery | None = None
        self.last_memories: tuple[RetrievedMemory, ...] | None = None
        self.result_override = result_override

    async def rank(
        self,
        query: MemoryQuery,
        memories: tuple[RetrievedMemory, ...],
    ) -> tuple[RetrievedMemory, ...]:
        """Record ranking inputs and return the configured result if present."""
        self.calls += 1
        self.last_query = query
        self.last_memories = memories

        if self.result_override is not None:
            return self.result_override

        return memories

    def reset(self) -> None:
        """Clear recorded ranking state."""
        self.calls = 0
        self.last_query = None
        self.last_memories = None
