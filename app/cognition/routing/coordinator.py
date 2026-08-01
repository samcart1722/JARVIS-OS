"""Deterministic coordinator for explicit typed local-first routing."""

from app.cognition.local_resolution.resolver import LocalFirstResolver
from app.cognition.routing.contracts import CognitiveProcessor
from app.cognition.routing.models import (
    CoordinatedRequest,
    CoordinatedResult,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)


class LocalFirstCognitiveCoordinator:
    def __init__(
        self,
        local_resolver: LocalFirstResolver,
        cognitive_processor: CognitiveProcessor,
    ) -> None:
        self._local_resolver = local_resolver
        self._cognitive_processor = cognitive_processor

    def coordinate(self, request: CoordinatedRequest) -> CoordinatedResult:
        if not isinstance(request, CoordinatedRequest):
            raise TypeError("A valid coordinated request is required.")
        local_result = self._local_resolver.resolve(
            request.actor,
            request.workspace,
            request.local_intent,
        )
        if local_result.handled:
            return CoordinatedResult(
                CoordinatedRoute.LOCAL,
                local_result=local_result,
            )
        if not request.fallback_authorization.allowed:
            return CoordinatedResult(
                CoordinatedRoute.SAFE_INSUFFICIENCY,
                insufficiency_reason=(
                    SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED
                ),
            )
        if not isinstance(request.cognitive_input, str) or not (
            request.cognitive_input.strip()
        ):
            return CoordinatedResult(
                CoordinatedRoute.SAFE_INSUFFICIENCY,
                insufficiency_reason=SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID,
            )
        cognitive_outcome = self._cognitive_processor.process(
            request.cognitive_input
        )
        return CoordinatedResult(
            CoordinatedRoute.COGNITIVE,
            cognitive_outcome=cognitive_outcome,
        )
