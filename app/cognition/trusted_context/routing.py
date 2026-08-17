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
from app.membership.models import MembershipDecision
from app.membership.service import MembershipDecisionService


class TrustedLocalCommandRoutingService:
    def __init__(
        self,
        resolver: TrustedRequestContextResolver,
        membership_service: MembershipDecisionService,
        router: LocalCommandTextRouter,
    ) -> None:
        if resolver is None:
            raise ValueError("A trusted request context resolver is required.")
        if membership_service is None:
            raise ValueError("A membership decision service is required.")
        if router is None:
            raise ValueError("A local command text router is required.")
        self._resolver = resolver
        self._membership_service = membership_service
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

        membership_decision = self._membership_service.decide(
            trust_resolution.context.actor,
            trust_resolution.context.workspace,
        )
        if type(membership_decision) is not MembershipDecision:
            raise TypeError("Membership service returned an invalid decision.")
        if not membership_decision.success:
            return TrustedLocalCommandRoutingResult(
                trust_resolution,
                membership_decision,
            )

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
            membership_decision,
            text_routing_result,
        )
