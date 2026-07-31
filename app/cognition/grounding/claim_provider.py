"""Reasoning provider decorator for claim-level evidence attribution."""

from typing import Protocol

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import GROUNDED_RESPONSE_PROTOCOL_INVALID
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.grounding.claim_models import ClaimGroundedResponseEnvelope
from app.cognition.grounding.claim_parser import ClaimEvidenceResponseParser
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.parser import GroundedResponseProtocolError
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
        *,
        enabled: bool,
    ) -> None:
        self._provider = provider
        self._parser = parser
        self._selector = evidence_selector
        self._formatter = formatter
        self._enabled = enabled

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
        return ReasoningResult(response=self._formatter.format(envelope))
