"""In-memory implementation of scope-isolated memory persistence."""

from collections.abc import Iterable

from app.cognition.memory.scoped.contracts import (
    ScopedMemoryRepository,
    ScopedMemoryWriter,
)
from app.cognition.memory.scoped.models import (
    MemoryScope,
    ScopedMemoryRecord,
)


class InMemoryScopedMemoryRepository(
    ScopedMemoryRepository,
    ScopedMemoryWriter,
):
    """Append and search ephemeral records without crossing scope boundaries."""

    def __init__(
        self,
        records: Iterable[ScopedMemoryRecord] = (),
    ) -> None:
        if isinstance(records, (str, bytes)):
            raise TypeError(
                "Initial scoped memory records must be a collection of records."
            )
        normalized_records = tuple(records)

        grouped: dict[MemoryScope, list[ScopedMemoryRecord]] = {}
        for record in normalized_records:
            if not isinstance(record, ScopedMemoryRecord):
                raise TypeError("Initial records must be scoped memory records.")
            grouped.setdefault(record.scope, []).append(record)

        self._records_by_scope = {
            scope: tuple(owned_records)
            for scope, owned_records in grouped.items()
        }

    def add(self, record: ScopedMemoryRecord) -> None:
        """Append exactly one validated record to its explicit scope bucket."""
        if not isinstance(record, ScopedMemoryRecord):
            raise TypeError("Added record must be a scoped memory record.")
        owned_records = self._records_by_scope.get(record.scope, ())
        self._records_by_scope[record.scope] = (*owned_records, record)

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
