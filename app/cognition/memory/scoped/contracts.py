"""Separate contracts for scope-isolated memory reads and explicit writes."""

from typing import Protocol

from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)


class ScopedMemoryRepository(Protocol):
    """Search memory records only within an explicitly supplied scope."""

    def search(
        self,
        scope: MemoryScope,
        query: str,
    ) -> tuple[ScopedMemoryRecord, ...]:
        """Return deterministic literal matches owned by the given scope."""


class ScopedMemoryWriter(Protocol):
    """Append already-validated records through an explicit write boundary."""

    def add(self, record: ScopedMemoryRecord) -> None:
        """Add exactly the supplied record without retrieval or transformation."""


class MemoryContextRetriever(Protocol):
    """Retrieve a scoped snapshot for cognitive context enrichment."""

    def retrieve(
        self,
        scope: MemoryScope,
        query: str,
    ) -> MemorySnapshot:
        """Return one immutable snapshot without modifying cognitive context."""
