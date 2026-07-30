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
