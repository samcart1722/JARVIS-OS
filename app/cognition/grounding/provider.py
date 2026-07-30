"""Reasoning-provider decorator enforcing evidence-bounded responses."""

from app.cognition.domain.cognitive_context import CognitiveContext
from app.cognition.domain.cognitive_outcome import (
    GROUNDED_RESPONSE_PROTOCOL_INVALID,
)
from app.cognition.domain.reasoning_result import ReasoningResult
from app.cognition.grounding.evidence import MemoryEvidenceSelector
from app.cognition.grounding.models import ANSWERED
from app.cognition.grounding.parser import (
    GroundedResponseParser,
    GroundedResponseProtocolError,
)
from app.cognition.providers.base_provider import ReasoningProvider

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "Insufficient scoped memory evidence to answer the current request."
)


class EvidenceBoundedReasoningProvider:
    """Validate grounded responses while preserving exact pass-through."""

    def __init__(
        self,
        provider: ReasoningProvider,
        parser: GroundedResponseParser,
        evidence_selector: MemoryEvidenceSelector,
        *,
        enabled: bool,
    ) -> None:
        self._provider = provider
        self._parser = parser
        self._evidence_selector = evidence_selector
        self._enabled = enabled

    def generate(self, context: CognitiveContext) -> ReasoningResult:
        """Call once and validate only when bounded evidence is active."""
        evidence = (
            self._evidence_selector.select(context)
            if self._enabled
            else ()
        )
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
        if envelope.status != ANSWERED:
            return ReasoningResult(response=INSUFFICIENT_EVIDENCE_MESSAGE)
        references = ", ".join(
            str(number) for number in envelope.used_record_numbers
        )
        return ReasoningResult(
            response=(
                f"{envelope.answer}\n"
                f"Evidence used: scoped memory records {references}."
            )
        )
