"""Pure deterministic formatting for claim-level evidence."""

from app.cognition.grounding.claim_models import ClaimGroundedResponseEnvelope
from app.cognition.grounding.models import ANSWERED, INSUFFICIENT_EVIDENCE_MESSAGE


class ClaimEvidenceFormatter:
    def format(self, envelope: ClaimGroundedResponseEnvelope) -> str:
        """Format a validated envelope without exposing scope or records."""
        if envelope.status != ANSWERED:
            return INSUFFICIENT_EVIDENCE_MESSAGE
        blocks = []
        for index, claim in enumerate(envelope.claims, start=1):
            references = ", ".join(map(str, claim.used_record_numbers))
            blocks.append(
                f"Claim {index}:\n{claim.text}\n"
                f"Evidence used: scoped memory records {references}."
            )
        return "\n\n".join(blocks)
