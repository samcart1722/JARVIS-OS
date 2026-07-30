"""Explicit, opt-in scoped memory update operation."""

from app.cognition.memory.scoped.contracts import ScopedMemoryWriter
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord


class MemoryUpdateDisabledError(RuntimeError):
    """Indicate that an explicit write was rejected by configuration."""


class ExplicitMemoryUpdateService:
    """Create and append one record only when deliberately invoked."""

    def __init__(
        self,
        writer: ScopedMemoryWriter,
        *,
        enabled: bool,
    ) -> None:
        self._writer = writer
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Expose immutable operational enablement."""
        return self._enabled

    def remember(
        self,
        scope: MemoryScope,
        content: str,
    ) -> ScopedMemoryRecord:
        """Append exactly one explicit record and return that same record."""
        if not self._enabled:
            raise MemoryUpdateDisabledError(
                "Explicit scoped memory update is disabled."
            )
        if not isinstance(scope, MemoryScope):
            raise TypeError("Explicit memory update requires a MemoryScope.")
        if not isinstance(content, str):
            raise TypeError("Explicit memory update content must be text.")
        record = ScopedMemoryRecord(scope=scope, content=content)
        self._writer.add(record)
        return record
