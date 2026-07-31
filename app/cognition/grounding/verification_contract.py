"""Pure contract for model-assisted claim evidence verification."""

from typing import Protocol

from app.cognition.grounding.claim_models import ClaimGroundedResponseEnvelope
from app.cognition.grounding.evidence import SelectedMemoryEvidence
from app.cognition.grounding.verification_models import (
    ClaimEvidenceVerificationResult,
)


class ClaimEvidenceVerifier(Protocol):
    def verify(
        self,
        envelope: ClaimGroundedResponseEnvelope,
        evidence: tuple[SelectedMemoryEvidence, ...],
    ) -> ClaimEvidenceVerificationResult: ...
