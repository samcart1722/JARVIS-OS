"""Repository-backed contextual memory retrieval."""

from app.cognition.memory.scoped.contracts import (
    MemoryContextRetriever,
    ScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import MemoryScope, MemorySnapshot


class RepositoryMemoryContextRetriever(MemoryContextRetriever):
    """Translate one scoped repository search into a context snapshot."""

    def __init__(self, repository: ScopedMemoryRepository) -> None:
        self._repository = repository

    def retrieve(
        self,
        scope: MemoryScope,
        query: str,
    ) -> MemorySnapshot:
        """Search once and preserve repository ordering in the snapshot."""
        records = self._repository.search(scope, query)
        return MemorySnapshot(scope=scope, records=records)
