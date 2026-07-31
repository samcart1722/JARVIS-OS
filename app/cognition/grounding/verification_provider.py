"""Ollama-backed adapter for one claim-support verification call."""

import requests

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
)
from app.cognition.grounding.claim_models import ClaimGroundedResponseEnvelope
from app.cognition.grounding.evidence import SelectedMemoryEvidence
from app.cognition.grounding.verification_contract import ClaimEvidenceVerifier
from app.cognition.grounding.verification_models import ClaimEvidenceVerificationResult
from app.cognition.grounding.verification_parser import (
    ClaimEvidenceVerificationParser,
    ClaimEvidenceVerificationProtocolError,
)
from app.cognition.grounding.verification_prompt import (
    ClaimEvidenceVerificationPromptBuilder,
)
from app.models.ollama_client import OllamaClient


class OllamaClaimEvidenceVerifier(ClaimEvidenceVerifier):
    def __init__(
        self,
        client: OllamaClient,
        prompt_builder: ClaimEvidenceVerificationPromptBuilder,
        parser: ClaimEvidenceVerificationParser,
    ) -> None:
        self._client = client
        self._prompt_builder = prompt_builder
        self._parser = parser

    def verify(
        self,
        envelope: ClaimGroundedResponseEnvelope,
        evidence: tuple[SelectedMemoryEvidence, ...],
    ) -> ClaimEvidenceVerificationResult:
        prompt = self._prompt_builder.build(envelope, evidence)
        try:
            raw_response = self._client.chat(prompt)
        except requests.RequestException:
            return ClaimEvidenceVerificationResult(
                error_code=CAPABILITY_EXECUTION_FAILED
            )
        try:
            verified = self._parser.parse(
                raw_response, claim_count=len(envelope.claims)
            )
        except ClaimEvidenceVerificationProtocolError:
            return ClaimEvidenceVerificationResult(
                error_code=CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID
            )
        return ClaimEvidenceVerificationResult(envelope=verified)
