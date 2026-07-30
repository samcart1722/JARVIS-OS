"""Immutable models for scope-owned memory records."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryScope:
    """Represent one opaque, explicitly supplied memory ownership boundary."""

    identifier: str

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("Memory scope identifier cannot be empty.")


@dataclass(frozen=True, slots=True)
class ScopedMemoryRecord:
    """Associate stable memory content with exactly one explicit scope."""

    scope: MemoryScope
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope, MemoryScope):
            raise TypeError("A scoped memory record requires a MemoryScope.")
        normalized_content = self.content.strip()
        if not normalized_content:
            raise ValueError("Memory content cannot be empty.")
        object.__setattr__(self, "content", normalized_content)


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """Represent one completed contextual retrieval for an explicit scope."""

    scope: MemoryScope
    records: tuple[ScopedMemoryRecord, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.scope, MemoryScope):
            raise TypeError("A memory snapshot requires a MemoryScope.")
        if not isinstance(self.records, tuple):
            raise TypeError("Memory snapshot records must be a tuple.")
        if any(record.scope != self.scope for record in self.records):
            raise ValueError("Memory snapshot records must match its scope.")
