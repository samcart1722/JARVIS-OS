import pickle
from dataclasses import asdict
from typing import Any, cast
from unittest.mock import patch

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.interpretation.routing import TextRoutingResult
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    LocalResolutionResult,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.routing.models import (
    CoordinatedResult,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)
from app.core.config import Settings
from app.core.container import Container
from app.local_command import (
    LOCAL_COMMAND_TEXT_MAX_LENGTH,
    WORKSPACE_ID_MAX_LENGTH,
    LocalCommandApplicationError,
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationGateway,
    LocalCommandApplicationRequest,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    application_error,
)
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
)
from app.principal_authentication.models import (
    AuthenticatedPrincipal,
    LocalAuthenticationProof,
    PrincipalActorMappingErrorCode,
    PrincipalActorMappingResult,
    PrincipalAuthenticationErrorCode,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)
from app.principal_authentication.routing import (
    AuthenticatedLocalCommandRequest,
    AuthenticatedLocalCommandRoutingResult,
    AuthenticatedWorkspaceSelectionErrorCode,
    AuthenticatedWorkspaceSelectionResult,
)


def _request(**overrides) -> LocalCommandApplicationRequest:
    values = {
        "proof": "super-secret-proof",
        "requested_workspace_id": "workspace",
        "text": "list read groceries",
        "allow_cognitive_fallback": False,
    }
    values.update(overrides)
    return LocalCommandApplicationRequest(**values)



def _gateway(
    service: object,
) -> LocalCommandApplicationGateway:
    return LocalCommandApplicationGateway(
        cast(Any, service)
    )


def _application_error_code(
    result: LocalCommandApplicationResult,
) -> LocalCommandApplicationErrorCode:
    assert result.error is not None
    return result.error.code

def test_application_request_is_immutable_and_normalizes_workspace_only() -> None:
    request = _request(
        requested_workspace_id="  workspace  ",
        text="  list read groceries  ",
    )

    assert request.requested_workspace_id == "workspace"
    assert request.text == "  list read groceries  "

    with pytest.raises(AttributeError, match="immutable"):
        cast(Any, request).text = "changed"


def test_application_request_repr_never_contains_proof() -> None:
    proof = "proof-that-must-never-appear"
    request = _request(proof=proof)

    representation = repr(request)

    assert proof not in representation
    assert "proof=" not in representation


@pytest.mark.parametrize(
    "proof",
    (
        None,
        "",
        "   ",
    ),
)
def test_application_request_rejects_missing_or_blank_proof(proof) -> None:
    with pytest.raises(ValueError, match="proof"):
        _request(proof=proof)


@pytest.mark.parametrize(
    "workspace_id",
    (
        "",
        "   ",
        123,
        None,
    ),
)
def test_application_request_rejects_invalid_workspace(workspace_id) -> None:
    with pytest.raises(ValueError, match="Workspace"):
        _request(requested_workspace_id=workspace_id)


def test_application_request_rejects_oversized_workspace() -> None:
    with pytest.raises(ValueError, match="too long"):
        _request(
            requested_workspace_id="w" * (WORKSPACE_ID_MAX_LENGTH + 1),
        )


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        123,
        None,
    ),
)
def test_application_request_rejects_invalid_text(text) -> None:
    with pytest.raises(ValueError, match="command text"):
        _request(text=text)


def test_application_request_rejects_oversized_text() -> None:
    with pytest.raises(ValueError, match="too long"):
        _request(
            text="x" * (LOCAL_COMMAND_TEXT_MAX_LENGTH + 1),
        )


@pytest.mark.parametrize(
    "fallback",
    (
        0,
        1,
        "false",
        "true",
        None,
    ),
)
def test_application_request_requires_strict_fallback_boolean(fallback) -> None:
    with pytest.raises(ValueError, match="explicit boolean"):
        _request(allow_cognitive_fallback=fallback)


@pytest.mark.parametrize(
    "fallback",
    (
        False,
        True,
    ),
)
def test_application_request_accepts_explicit_fallback_boolean(fallback) -> None:
    request = _request(allow_cognitive_fallback=fallback)

    assert request.allow_cognitive_fallback is fallback


@pytest.mark.parametrize(
    "code",
    tuple(LocalCommandApplicationErrorCode),
)
def test_application_error_factory_produces_canonical_closed_errors(code) -> None:
    error = application_error(code)

    assert error.code is code
    assert error.message


def test_local_validation_failure_message_is_non_blaming() -> None:
    error = application_error(
        LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED
    )

    assert error.message == "The local operation could not be completed."
    assert "invalid" not in error.message.lower()


def test_application_error_rejects_noncanonical_message() -> None:
    with pytest.raises(ValueError, match="canonical"):
        LocalCommandApplicationError(
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
            "Wrong message.",
        )


@pytest.mark.parametrize(
    "route",
    (
        LocalCommandApplicationRoute.LOCAL,
        LocalCommandApplicationRoute.COGNITIVE,
    ),
)
def test_successful_application_result_requires_usable_route(route) -> None:
    result = LocalCommandApplicationResult(
        True,
        route=route,
        response="completed",
    )

    assert result.success
    assert result.route is route
    assert result.response == "completed"
    assert result.error is None


def test_successful_application_result_rejects_safe_insufficiency() -> None:
    with pytest.raises(ValueError, match="usable route"):
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            response="completed",
        )


@pytest.mark.parametrize(
    "response",
    (
        None,
        "",
        "   ",
    ),
)
def test_successful_application_result_requires_nonblank_response(response) -> None:
    with pytest.raises(ValueError, match="requires a response"):
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response=response,
        )


def test_failed_application_result_allows_precoordination_route_none() -> None:
    error = application_error(
        LocalCommandApplicationErrorCode.ACCESS_DENIED
    )

    result = LocalCommandApplicationResult(
        False,
        error=error,
    )

    assert not result.success
    assert result.route is None
    assert result.response is None
    assert result.error is error


def test_failed_application_result_allows_safe_insufficiency_route() -> None:
    error = application_error(
        LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED
    )

    result = LocalCommandApplicationResult(
        False,
        route=LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
        error=error,
    )

    assert not result.success
    assert result.route is LocalCommandApplicationRoute.SAFE_INSUFFICIENCY
    assert result.response is None
    assert result.error is error


def test_failed_application_result_requires_error() -> None:
    with pytest.raises(ValueError, match="requires an application error"):
        LocalCommandApplicationResult(False)


def test_failed_application_result_forbids_response() -> None:
    with pytest.raises(ValueError, match="forbids a response"):
        LocalCommandApplicationResult(
            False,
            response="should not exist",
            error=application_error(
                LocalCommandApplicationErrorCode.INTERNAL_ERROR
            ),
        )

class RecordingRoutingService:
    def __init__(self, result) -> None:
        self.result = result
        self.requests = []

    def route(self, request):
        self.requests.append(request)
        return self.result


def _authentication_success() -> PrincipalAuthenticationResult:
    return PrincipalAuthenticationResult(
        True,
        AuthenticatedPrincipal(
            PrincipalIdentity("principal")
        ),
    )


def _mapping_success() -> PrincipalActorMappingResult:
    return PrincipalActorMappingResult(
        True,
        ActorIdentity("actor"),
    )


def _selection_success() -> AuthenticatedWorkspaceSelectionResult:
    return AuthenticatedWorkspaceSelectionResult(
        True,
        WorkspaceIdentity("workspace"),
    )


def _membership_success() -> MembershipDecision:
    return MembershipDecision(
        True,
        ActorWorkspaceMembership(
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            MembershipStatus.ACTIVE,
        ),
    )


def _interpreted() -> LocalCommandInterpretation:
    return LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INTERPRETED,
        ReadListItemsQuery("groceries"),
    )


def _not_interpreted() -> LocalCommandInterpretation:
    return LocalCommandInterpretation(
        LocalCommandInterpretationStatus.NOT_INTERPRETED
    )


def _full_result(
    text_routing: TextRoutingResult,
) -> AuthenticatedLocalCommandRoutingResult:
    return AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        _mapping_success(),
        _selection_success(),
        _membership_success(),
        text_routing,
    )


def _local_text_result(
    *,
    success: bool,
    response: str,
    error_code: str | None = None,
) -> TextRoutingResult:
    local_result = LocalResolutionResult(
        True,
        success,
        response,
        LOCAL_CAPABILITY_ROUTE,
        error_code=error_code,
    )
    return TextRoutingResult(
        _interpreted(),
        CoordinatedResult(
            CoordinatedRoute.LOCAL,
            local_result=local_result,
        ),
    )


def test_gateway_constructs_one_internal_authenticated_request() -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        PrincipalAuthenticationResult(
            False,
            error_code=(
                PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED
            ),
        )
    )
    service = RecordingRoutingService(routed)
    gateway = _gateway(service)
    proof = "proof-that-must-remain-secret"

    result = gateway.execute(
        _request(
            proof=proof,
            allow_cognitive_fallback=True,
        )
    )

    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.ACCESS_DENIED
    )
    assert len(service.requests) == 1

    internal = service.requests[0]

    assert type(internal) is AuthenticatedLocalCommandRequest
    assert type(internal.authentication_proof) is LocalAuthenticationProof
    assert internal.authentication_proof.proof == proof
    assert internal.requested_workspace_id == "workspace"
    assert internal.text == "list read groceries"
    assert internal.fallback_authorization.allowed is True
    assert proof not in repr(internal.authentication_proof)
    assert proof not in repr(internal)


def test_gateway_rejects_invalid_application_request_without_routing() -> None:
    service = RecordingRoutingService(object())
    gateway = _gateway(service)

    with pytest.raises(TypeError, match="application request"):
        gateway.execute(cast(Any, object()))

    assert service.requests == []


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            PrincipalAuthenticationErrorCode.AUTHENTICATION_RESOLUTION_FAILED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
        ),
    ),
)
def test_gateway_maps_authentication_failures(
    internal_code,
    expected,
) -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        PrincipalAuthenticationResult(
            False,
            error_code=internal_code,
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert _application_error_code(result) is expected


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
        ),
    ),
)
def test_gateway_maps_principal_mapping_failures(
    internal_code,
    expected,
) -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        PrincipalActorMappingResult(
            False,
            error_code=internal_code,
        ),
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert _application_error_code(result) is expected


def test_gateway_maps_invalid_workspace_selection() -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        _mapping_success(),
        AuthenticatedWorkspaceSelectionResult(
            False,
            error_code=(
                AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
            ),
        ),
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.INVALID_REQUEST
    )


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            MEMBERSHIP_NOT_FOUND,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            MEMBERSHIP_INACTIVE,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            MEMBERSHIP_RESOLUTION_FAILED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
        ),
    ),
)
def test_gateway_maps_membership_failures(
    internal_code,
    expected,
) -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        _mapping_success(),
        _selection_success(),
        MembershipDecision(
            False,
            error_code=internal_code,
        ),
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert _application_error_code(result) is expected


def test_gateway_maps_invalid_interpretation_to_invalid_request() -> None:
    interpretation = LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INVALID,
        invalid_reason=LocalCommandInvalidReason.INVALID_INPUT,
    )
    routed = _full_result(
        TextRoutingResult(interpretation)
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.INVALID_REQUEST
    )


def test_gateway_maps_local_success() -> None:
    routed = _full_result(
        _local_text_result(
            success=True,
            response="List read locally.",
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert result.response == "List read locally."
    assert result.error is None


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            LOCAL_PERMISSION_DENIED,
            LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED,
        ),
        (
            LOCAL_VALIDATION_FAILED,
            LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED,
        ),
        (
            LOCAL_KNOWLEDGE_NOT_FOUND,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND,
        ),
        (
            LOCAL_KNOWLEDGE_CONFLICT,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT,
        ),
    ),
)
def test_gateway_maps_known_local_failures(
    internal_code,
    expected,
) -> None:
    routed = _full_result(
        _local_text_result(
            success=False,
            response="Local operation failed.",
            error_code=internal_code,
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert result.response is None
    assert _application_error_code(result) is expected


@pytest.mark.parametrize(
    ("reason", "expected"),
    (
        (
            SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED,
            LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED,
        ),
        (
            SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID,
            LocalCommandApplicationErrorCode.INVALID_REQUEST,
        ),
    ),
)
def test_gateway_maps_safe_insufficiency(
    reason,
    expected,
) -> None:
    routed = _full_result(
        TextRoutingResult(
            _not_interpreted(),
            CoordinatedResult(
                CoordinatedRoute.SAFE_INSUFFICIENCY,
                insufficiency_reason=reason,
            ),
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert (
        result.route
        is LocalCommandApplicationRoute.SAFE_INSUFFICIENCY
    )
    assert _application_error_code(result) is expected


def test_gateway_maps_cognitive_success() -> None:
    routed = _full_result(
        TextRoutingResult(
            _not_interpreted(),
            CoordinatedResult(
                CoordinatedRoute.COGNITIVE,
                cognitive_outcome=CognitiveOutcome(
                    True,
                    response="Cognitive answer.",
                ),
            ),
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(
        _request(allow_cognitive_fallback=True)
    )

    assert result.success
    assert result.route is LocalCommandApplicationRoute.COGNITIVE
    assert result.response == "Cognitive answer."
    assert result.error is None


def test_gateway_collapses_controlled_cognitive_failure() -> None:
    routed = _full_result(
        TextRoutingResult(
            _not_interpreted(),
            CoordinatedResult(
                CoordinatedRoute.COGNITIVE,
                cognitive_outcome=CognitiveOutcome(
                    False,
                    error=cognitive_error(
                        CAPABILITY_EXECUTION_FAILED
                    ),
                ),
            ),
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(
        _request(allow_cognitive_fallback=True)
    )

    assert not result.success
    assert result.route is LocalCommandApplicationRoute.COGNITIVE
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED
    )


def test_gateway_rejects_invalid_routing_result_type() -> None:
    gateway = _gateway(RecordingRoutingService(object()))

    with pytest.raises(
        TypeError,
        match="invalid result",
    ):
        gateway.execute(_request())


def test_gateway_rejects_unknown_local_failure() -> None:
    routed = _full_result(
        _local_text_result(
            success=False,
            response="Local operation failed.",
            error_code="unknown_local_failure",
        )
    )

    gateway = _gateway(RecordingRoutingService(routed))

    with pytest.raises(
        TypeError,
        match="unknown failure",
    ):
        gateway.execute(_request())

def test_application_request_has_no_generic_dataclass_serialization() -> None:
    proof = "proof-that-must-never-serialize"
    request = _request(proof=proof)

    with pytest.raises(TypeError):
        asdict(cast(Any, request))

    with pytest.raises(TypeError):
        vars(request)

    assert not hasattr(request, "__dict__")


@pytest.mark.parametrize(
    "protocol",
    range(pickle.HIGHEST_PROTOCOL + 1),
)
def test_application_request_rejects_pickle_serialization(
    protocol: int,
) -> None:
    proof = "proof-that-must-never-be-pickled"
    request = _request(proof=proof)

    with pytest.raises(TypeError) as exc_info:
        pickle.dumps(
            request,
            protocol=protocol,
        )

    message = str(exc_info.value)

    assert "serialization is prohibited" in message
    assert proof not in message
    assert proof not in repr(exc_info.value)


@pytest.mark.parametrize(
    ("route", "code"),
    (
        (
            LocalCommandApplicationRoute.LOCAL,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            LocalCommandApplicationRoute.COGNITIVE,
            LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED,
        ),
        (
            LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED,
        ),
        (
            None,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND,
        ),
    ),
)
def test_failed_application_result_rejects_incoherent_route_error_pair(
    route,
    code,
) -> None:
    with pytest.raises(
        ValueError,
        match="route and error are inconsistent",
    ):
        LocalCommandApplicationResult(
            False,
            route=route,
            error=application_error(code),
        )


def test_internal_error_is_valid_only_before_route_classification() -> None:
    result = LocalCommandApplicationResult(
        False,
        error=application_error(
            LocalCommandApplicationErrorCode.INTERNAL_ERROR
        ),
    )

    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.INTERNAL_ERROR
    )

def test_container_composes_one_application_gateway_from_authenticated_route() -> None:
    container = Container(cast(Any, Settings)(_env_file=None))

    gateway = container.local_command_application_gateway

    assert type(gateway) is LocalCommandApplicationGateway
    assert (
        gateway._routing_service
        is container.authenticated_local_command_routing_service
    )


def test_default_container_application_gateway_fails_closed_before_downstream() -> None:
    container = Container(cast(Any, Settings)(_env_file=None))

    with (
        patch(
            "app.principal_authentication.configured_mapper."
            "ConfiguredPrincipalActorMapper.map"
        ) as map_principal,
        patch(
            "app.membership.service."
            "MembershipDecisionService.decide"
        ) as decide_membership,
        patch(
            "app.cognition.interpretation.routing."
            "LocalCommandTextRouter.route"
        ) as route_text,
    ):
        result = container.local_command_application_gateway.execute(
            _request()
        )

    assert not result.success
    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.ACCESS_DENIED
    )

    map_principal.assert_not_called()
    decide_membership.assert_not_called()
    route_text.assert_not_called()
