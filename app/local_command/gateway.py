"""Application gateway over the governed authenticated local-command route."""

from app.cognition.domain.cognitive_outcome import COGNITIVE_ERROR_CODES
from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.local_resolution.models import (
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
)
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)
from app.local_command.models import (
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationRequest,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    application_error,
)
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
)
from app.principal_authentication.models import (
    LocalAuthenticationProof,
    PrincipalActorMappingErrorCode,
    PrincipalAuthenticationErrorCode,
)
from app.principal_authentication.routing import (
    AuthenticatedLocalCommandRequest,
    AuthenticatedLocalCommandRoutingResult,
    AuthenticatedLocalCommandRoutingService,
    AuthenticatedWorkspaceSelectionErrorCode,
)

_LOCAL_ERROR_MAP = {
    LOCAL_PERMISSION_DENIED: (
        LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED
    ),
    LOCAL_VALIDATION_FAILED: (
        LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED
    ),
    LOCAL_KNOWLEDGE_NOT_FOUND: (
        LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND
    ),
    LOCAL_KNOWLEDGE_CONFLICT: (
        LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT
    ),
}


class LocalCommandApplicationGateway:
    """Translate one safe application request through the governed route."""

    __slots__ = ("_routing_service",)

    def __init__(
        self,
        routing_service: AuthenticatedLocalCommandRoutingService,
    ) -> None:
        if routing_service is None:
            raise ValueError(
                "An authenticated local-command routing service is required."
            )
        self._routing_service = routing_service

    def execute(
        self,
        request: LocalCommandApplicationRequest,
    ) -> LocalCommandApplicationResult:
        if type(request) is not LocalCommandApplicationRequest:
            raise TypeError(
                "A valid local-command application request is required."
            )

        routed = self._routing_service.route(
            AuthenticatedLocalCommandRequest(
                authentication_proof=LocalAuthenticationProof(
                    request.proof
                ),
                requested_workspace_id=request.requested_workspace_id,
                text=request.text,
                fallback_authorization=CognitiveFallbackAuthorization(
                    request.allow_cognitive_fallback
                ),
            )
        )

        if type(routed) is not AuthenticatedLocalCommandRoutingResult:
            raise TypeError(
                "Authenticated routing returned an invalid result."
            )

        return self._map_routed_result(routed)

    def _map_routed_result(
        self,
        routed: AuthenticatedLocalCommandRoutingResult,
    ) -> LocalCommandApplicationResult:
        authentication = routed.authentication_result

        if not authentication.success:
            if (
                authentication.error_code
                is PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.ACCESS_DENIED
                )
            if (
                authentication.error_code
                is PrincipalAuthenticationErrorCode.AUTHENTICATION_RESOLUTION_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE
                )
            raise TypeError(
                "Authentication result contains an unknown failure."
            )

        mapping = routed.mapping_result
        if mapping is None:
            raise TypeError(
                "Authenticated routing omitted principal mapping."
            )

        if not mapping.success:
            if (
                mapping.error_code
                is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.ACCESS_DENIED
                )
            if (
                mapping.error_code
                is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE
                )
            raise TypeError(
                "Principal mapping contains an unknown failure."
            )

        selection = routed.workspace_selection_result
        if selection is None:
            raise TypeError(
                "Authenticated routing omitted workspace selection."
            )

        if not selection.success:
            if (
                selection.error_code
                is AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.INVALID_REQUEST
                )
            raise TypeError(
                "Workspace selection contains an unknown failure."
            )

        membership = routed.membership_decision
        if membership is None:
            raise TypeError(
                "Authenticated routing omitted membership decision."
            )

        if not membership.success:
            if membership.error_code in (
                MEMBERSHIP_NOT_FOUND,
                MEMBERSHIP_INACTIVE,
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.ACCESS_DENIED
                )
            if membership.error_code == MEMBERSHIP_RESOLUTION_FAILED:
                return self._failure(
                    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE
                )
            raise TypeError(
                "Membership decision contains an unknown failure."
            )

        text_routing = routed.text_routing_result
        if text_routing is None:
            raise TypeError(
                "Authenticated routing omitted text-routing result."
            )

        if (
            text_routing.interpretation.status
            is LocalCommandInterpretationStatus.INVALID
        ):
            return self._failure(
                LocalCommandApplicationErrorCode.INVALID_REQUEST
            )

        coordinated = text_routing.coordinated_result
        if coordinated is None:
            raise TypeError(
                "Text routing omitted coordinated result."
            )

        if coordinated.route is CoordinatedRoute.LOCAL:
            return self._map_local_result(coordinated.local_result)

        if coordinated.route is CoordinatedRoute.SAFE_INSUFFICIENCY:
            return self._map_safe_insufficiency(
                coordinated.insufficiency_reason
            )

        if coordinated.route is CoordinatedRoute.COGNITIVE:
            return self._map_cognitive_result(
                coordinated.cognitive_outcome
            )

        raise TypeError("Coordinated result contains an unknown route.")

    def _map_local_result(
        self,
        local_result,
    ) -> LocalCommandApplicationResult:
        if local_result is None:
            raise TypeError(
                "Local coordinated route omitted the local result."
            )

        if local_result.success:
            return LocalCommandApplicationResult(
                True,
                route=LocalCommandApplicationRoute.LOCAL,
                response=local_result.response,
            )

        error_code = _LOCAL_ERROR_MAP.get(local_result.error_code)
        if error_code is None:
            raise TypeError(
                "Local result contains an unknown failure."
            )

        return self._failure(
            error_code,
            LocalCommandApplicationRoute.LOCAL,
        )

    def _map_safe_insufficiency(
        self,
        reason,
    ) -> LocalCommandApplicationResult:
        if reason is SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED:
            return self._failure(
                LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED,
                LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            )

        if reason is SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID:
            return self._failure(
                LocalCommandApplicationErrorCode.INVALID_REQUEST,
                LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            )

        raise TypeError(
            "Safe-insufficiency result contains an unknown reason."
        )

    def _map_cognitive_result(
        self,
        outcome,
    ) -> LocalCommandApplicationResult:
        if outcome is None:
            raise TypeError(
                "Cognitive coordinated route omitted the outcome."
            )

        if outcome.success:
            return LocalCommandApplicationResult(
                True,
                route=LocalCommandApplicationRoute.COGNITIVE,
                response=outcome.response,
            )

        if (
            outcome.error is None
            or outcome.error.code not in COGNITIVE_ERROR_CODES
        ):
            raise TypeError(
                "Cognitive result contains an unknown failure."
            )

        return self._failure(
            LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED,
            LocalCommandApplicationRoute.COGNITIVE,
        )

    @staticmethod
    def _failure(
        code: LocalCommandApplicationErrorCode,
        route: LocalCommandApplicationRoute | None = None,
    ) -> LocalCommandApplicationResult:
        return LocalCommandApplicationResult(
            False,
            route=route,
            error=application_error(code),
        )