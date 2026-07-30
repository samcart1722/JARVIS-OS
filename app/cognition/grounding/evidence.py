"""Deterministic bounded selection of scoped memory evidence."""

from dataclasses import dataclass

from app.cognition.domain.cognitive_context import CognitiveContext


@dataclass(frozen=True, slots=True)
class SelectedMemoryEvidence:
    """One numbered content fragment available to the grounded protocol."""

    number: int
    content: str


class MemoryEvidenceSelector:
    """Apply existing record and character limits without ranking."""

    def __init__(self, *, max_records: int, max_characters: int) -> None:
        if max_records <= 0:
            raise ValueError("Memory evidence record limit must be positive.")
        if max_characters <= 0:
            raise ValueError("Memory evidence character limit must be positive.")
        self.max_records = max_records
        self.max_characters = max_characters

    def select(
        self,
        context: CognitiveContext,
    ) -> tuple[SelectedMemoryEvidence, ...]:
        """Select stable numbered fragments from the current snapshot."""
        snapshot = context.memory_snapshot
        if snapshot is None or not snapshot.records:
            return ()
        remaining = self.max_characters
        selected: list[SelectedMemoryEvidence] = []
        for record in snapshot.records[: self.max_records]:
            if remaining == 0:
                break
            fragment = record.content[:remaining]
            selected.append(
                SelectedMemoryEvidence(
                    number=len(selected) + 1,
                    content=fragment,
                )
            )
            remaining -= len(fragment)
        return tuple(selected)
