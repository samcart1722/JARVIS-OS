"""Immutable models for the evidence-bounded response protocol."""

from dataclasses import dataclass

ANSWERED = "answered"
INSUFFICIENT_EVIDENCE = "insufficient_evidence"
GROUNDED_STATUSES = frozenset((ANSWERED, INSUFFICIENT_EVIDENCE))


@dataclass(frozen=True, slots=True)
class GroundedResponseEnvelope:
    """Represent one validated evidence-bounded model response."""

    status: str
    answer: str
    used_record_numbers: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.status not in GROUNDED_STATUSES:
            raise ValueError("Unknown grounded response status.")
        if not isinstance(self.answer, str):
            raise TypeError("Grounded response answer must be text.")
        if not isinstance(self.used_record_numbers, tuple):
            raise TypeError("Grounded response references must be a tuple.")
        if any(type(number) is not int for number in self.used_record_numbers):
            raise TypeError("Grounded response references must be integers.")
        if any(number <= 0 for number in self.used_record_numbers):
            raise ValueError("Grounded response references must be positive.")
        if len(set(self.used_record_numbers)) != len(self.used_record_numbers):
            raise ValueError("Grounded response references must be unique.")
        if self.status == ANSWERED:
            if not self.answer.strip():
                raise ValueError("Answered response requires an answer.")
            if not self.used_record_numbers:
                raise ValueError("Answered response requires evidence references.")
            return
        if self.used_record_numbers:
            raise ValueError(
                "Insufficient-evidence response cannot cite records."
            )
