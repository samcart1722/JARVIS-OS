"""Reasoning provider decorator for claim-level evidence attribution."""

from typing import Protocol

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import (
    CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
    COGNITIVE_ERROR_CODES,
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
)
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.grounding.claim_models import ClaimGroundedResponseEnvelope
from app.cognition.grounding.claim_parser import ClaimEvidenceResponseParser
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.models import ANSWERED, INSUFFICIENT_EVIDENCE_MESSAGE
from app.cognition.grounding.parser import GroundedResponseProtocolError
from app.cognition.grounding.verification_contract import ClaimEvidenceVerifier
from app.cognition.providers.base_provider import ReasoningProvider


class ClaimEvidenceFormatting(Protocol):
    def format(self, envelope: ClaimGroundedResponseEnvelope) -> str: ...


class ClaimEvidenceAttributionProvider:
    def __init__(
        self,
        provider: ReasoningProvider,
        parser: ClaimEvidenceResponseParser,
        evidence_selector: MemoryEvidenceSelector,
        formatter: ClaimEvidenceFormatting,
        verifier: ClaimEvidenceVerifier | None = None,
        *,
        enabled: bool,
    ) -> None:
        self._provider = provider
        self._parser = parser
        self._selector = evidence_selector
        self._formatter = formatter
        self._enabled = enabled
        self._verifier = verifier

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        evidence = self._selector.select(context) if self._enabled else ()
        result = self._provider.generate(context)
        if not evidence or result.error_code is not None:
            return result
        try:
            envelope = self._parser.parse(
                result.response,
                max_record_number=len(evidence),
            )
        except GroundedResponseProtocolError:
            return ReasoningResult(
                response="",
                error_code=GROUNDED_RESPONSE_PROTOCOL_INVALID,
            )
        if envelope.status == ANSWERED and self._verifier is not None:
            verification = self._verifier.verify(envelope, evidence)
            if verification.error_code is not None:
                error_code = (
                    verification.error_code
                    if verification.error_code in COGNITIVE_ERROR_CODES
                    else CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID
                )
                return ReasoningResult(response="", error_code=error_code)
            verified = verification.envelope
            expected_numbers = set(range(1, len(envelope.claims) + 1))
            if (
                verified is None
                or len(verified.claims) != len(envelope.claims)
                or {item.claim_number for item in verified.claims} != expected_numbers
            ):
                return ReasoningResult(
                    response="",
                    error_code=CLAIM_EVIDENCE_VERIFICATION_PROTOCOL_INVALID,
                )
            if not verified.all_supported:
                return ReasoningResult(response=INSUFFICIENT_EVIDENCE_MESSAGE)
        return ReasoningResult(response=self._formatter.format(envelope))
