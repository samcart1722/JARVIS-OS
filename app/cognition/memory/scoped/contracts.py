"""Contract for scope-isolated, read-only memory persistence."""

from typing import Protocol

from app.cognition.memory.scoped.models import (
    MemoryScope,
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

