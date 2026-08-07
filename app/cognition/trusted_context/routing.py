"""Application sequencing for trusted local command routing."""

from app.cognition.interpretation.routing import (
    LocalCommandTextRouter,
    TextRoutingRequest,
    TextRoutingResult,
)
from app.cognition.trusted_context.contracts import TrustedRequestContextResolver
from app.cognition.trusted_context.models import (
    TrustedLocalCommandRequest,
    TrustedLocalCommandRoutingResult,
    TrustedRequestContextResolution,
)


class TrustedLocalCommandRoutingService:
    def __init__(
        self,
        resolver: TrustedRequestContextResolver,
        router: LocalCommandTextRouter,
    ) -> None:
        if resolver is None:
            raise ValueError("A trusted request context resolver is required.")
        if router is None:
            raise ValueError("A local command text router is required.")
        self._resolver = resolver
        self._router = router

    def route(
        self,
        request: TrustedLocalCommandRequest,
    ) -> TrustedLocalCommandRoutingResult:
        if type(request) is not TrustedLocalCommandRequest:
            raise TypeError("A valid trusted local command request is required.")

        trust_resolution = self._resolver.resolve(request.host_input)
        if type(trust_resolution) is not TrustedRequestContextResolution:
            raise TypeError("Resolver returned an invalid trusted context result.")
        if not trust_resolution.success:
            return TrustedLocalCommandRoutingResult(trust_resolution)

        text_routing_result = self._router.route(
            TextRoutingRequest(
                actor=trust_resolution.context.actor,
                workspace=trust_resolution.context.workspace,
                text=request.text,
                fallback_authorization=request.fallback_authorization,
            )
        )
        if type(text_routing_result) is not TextRoutingResult:
            raise TypeError("Router returned an invalid text routing result.")
        return TrustedLocalCommandRoutingResult(
            trust_resolution,
            text_routing_result,
        )
