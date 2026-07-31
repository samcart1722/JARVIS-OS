"""Immutable models for model-assisted claim support verification."""

from dataclasses import dataclass

VERIFIED = "verified"
SUPPORTED = "supported"
UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ClaimSupportVerdict:
    claim_number: int
    verdict: str

    def __post_init__(self) -> None:
        if type(self.claim_number) is not int:
            raise TypeError("Claim number must be an integer.")
        if self.claim_number <= 0:
            raise ValueError("Claim number must be positive.")
        if type(self.verdict) is not str:
            raise TypeError("Claim support verdict must be text.")
        if self.verdict not in (SUPPORTED, UNSUPPORTED):
            raise ValueError("Unknown claim support verdict.")


@dataclass(frozen=True, slots=True)
class ClaimEvidenceVerificationEnvelope:
    status: str
    claims: tuple[ClaimSupportVerdict, ...]

    def __post_init__(self) -> None:
        if self.status != VERIFIED:
            raise ValueError("Unknown verification status.")
        if not isinstance(self.claims, tuple):
            raise TypeError("Verification claims must be a tuple.")
        if any(not isinstance(item, ClaimSupportVerdict) for item in self.claims):
            raise TypeError("Verification claims contain invalid values.")
        if not self.claims:
            raise ValueError("Verification envelope requires claim verdicts.")
        numbers = tuple(item.claim_number for item in self.claims)
        if len(set(numbers)) != len(numbers):
            raise ValueError("Verification claim numbers must be unique.")

    @property
    def all_supported(self) -> bool:
        return all(item.verdict == SUPPORTED for item in self.claims)


@dataclass(frozen=True, slots=True)
class ClaimEvidenceVerificationResult:
    envelope: ClaimEvidenceVerificationEnvelope | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if (self.envelope is None) == (self.error_code is None):
            raise ValueError("Verification result requires one outcome.")
        if self.envelope is not None and not isinstance(
            self.envelope, ClaimEvidenceVerificationEnvelope
        ):
            raise TypeError("Verification envelope has an invalid type.")
        if self.error_code is not None and (
            type(self.error_code) is not str or not self.error_code.strip()
        ):
            raise ValueError("Verification error code must be non-empty text.")
