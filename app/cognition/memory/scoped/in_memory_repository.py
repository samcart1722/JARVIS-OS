"""In-memory implementation of scope-isolated memory persistence."""

from app.cognition.memory.scoped.contracts import ScopedMemoryRepository
from app.cognition.memory.scoped.models import (
    MemoryScope,
    ScopedMemoryRecord,
)


class InMemoryScopedMemoryRepository(ScopedMemoryRepository):
    """Search immutable constructor records without crossing scope boundaries."""

    def __init__(
        self,
        records: tuple[ScopedMemoryRecord, ...] = (),
    ) -> None:
        if not isinstance(records, tuple):
            raise TypeError("Initial scoped memory records must be a tuple.")

        grouped: dict[MemoryScope, list[ScopedMemoryRecord]] = {}
        for record in records:
            if not isinstance(record, ScopedMemoryRecord):
                raise TypeError("Initial records must be scoped memory records.")
            grouped.setdefault(record.scope, []).append(record)

        self._records_by_scope = {
            scope: tuple(owned_records)
            for scope, owned_records in grouped.items()
        }

    def search(
        self,
        scope: MemoryScope,
        query: str,
    ) -> tuple[ScopedMemoryRecord, ...]:
        """Match content literally after selecting only the requested scope."""
        if not isinstance(scope, MemoryScope):
            raise TypeError("Search requires an explicit MemoryScope.")
        normalized_query = query.strip().casefold()
        if not normalized_query:
            raise ValueError("Memory search query cannot be empty.")

        owned_records = self._records_by_scope.get(scope, ())
        return tuple(
            record
            for record in owned_records
            if normalized_query in record.content.casefold()
        )
