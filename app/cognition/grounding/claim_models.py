"""Immutable models for claim-level evidence attribution."""

from dataclasses import dataclass

from app.cognition.grounding.models import (
    ANSWERED,
    INSUFFICIENT_EVIDENCE,
)


@dataclass(frozen=True, slots=True)
class ClaimEvidence:
    """One textual claim and its ordered scoped-memory references."""

    text: str
    used_record_numbers: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("Claim text must be text.")
        if not self.text.strip():
            raise ValueError("Claim text cannot be empty.")
        if "\r" in self.text or "\n" in self.text:
            raise ValueError("Claim text must be a single line.")
        if not isinstance(self.used_record_numbers, tuple):
            raise TypeError("Claim references must be a tuple.")
        if not self.used_record_numbers:
            raise ValueError("Claim requires evidence references.")
        if any(type(number) is not int for number in self.used_record_numbers):
            raise TypeError("Claim references must be integers.")
        if any(number <= 0 for number in self.used_record_numbers):
            raise ValueError("Claim references must be positive.")
        if len(set(self.used_record_numbers)) != len(self.used_record_numbers):
            raise ValueError("Claim references must be unique.")


@dataclass(frozen=True, slots=True)
class ClaimGroundedResponseEnvelope:
    """Validated claim-level response envelope."""

    status: str
    claims: tuple[ClaimEvidence, ...]

    def __post_init__(self) -> None:
        if self.status not in (ANSWERED, INSUFFICIENT_EVIDENCE):
            raise ValueError("Unknown claim response status.")
        if not isinstance(self.claims, tuple):
            raise TypeError("Claims must be a tuple.")
        if any(not isinstance(claim, ClaimEvidence) for claim in self.claims):
            raise TypeError("Claims must contain ClaimEvidence values.")
        if self.status == ANSWERED and not self.claims:
            raise ValueError("Answered response requires claims.")
        if self.status == INSUFFICIENT_EVIDENCE and self.claims:
            raise ValueError("Insufficient-evidence response requires no claims.")
