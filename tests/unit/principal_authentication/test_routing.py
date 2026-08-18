from dataclasses import FrozenInstanceError, fields
from unittest.mock import Mock

import pytest

from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.interpretation.routing import TextRoutingResult
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.membership import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
)
from app.principal_authentication import (
    AuthenticatedLocalCommandRequest,
    AuthenticatedLocalCommandRoutingResult,
    AuthenticatedLocalCommandRoutingService,
    AuthenticatedPrincipal,
    AuthenticatedWorkspaceSelectionErrorCode,
    AuthenticatedWorkspaceSelectionResult,
    LocalAuthenticationProof,
    PrincipalActorMappingErrorCode,
    PrincipalActorMappingResult,
    PrincipalAuthenticationErrorCode,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)


def _authentication(success: bool = True) -> PrincipalAuthenticationResult:
    if success:
        return PrincipalAuthenticationResult(
            True, AuthenticatedPrincipal(PrincipalIdentity("principal"))
        )
    return PrincipalAuthenticationResult(
        False,
        error_code=PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
    )


def _mapping(success: bool = True, actor: ActorIdentity | None = None):
    if success:
        return PrincipalActorMappingResult(True, actor or ActorIdentity("actor"))
    return PrincipalActorMappingResult(
        False,
        error_code=PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
    )


def _selection(success: bool = True):
    if success:
        return AuthenticatedWorkspaceSelectionResult(
            True, WorkspaceIdentity("workspace")
        )
    return AuthenticatedWorkspaceSelectionResult(
        False,
        error_code=(
            AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
        ),
    )


def _membership(
    success: bool = True,
    actor: ActorIdentity | None = None,
    workspace: WorkspaceIdentity | None = None,
    error: str = MEMBERSHIP_NOT_FOUND,
):
    if success:
        return MembershipDecision(
            True,
            ActorWorkspaceMembership(
                actor or ActorIdentity("actor"),
                workspace or WorkspaceIdentity("workspace"),
                MembershipStatus.ACTIVE,
            ),
        )
    return MembershipDecision(False, error_code=error)


def _text_result() -> TextRoutingResult:
    return TextRoutingResult(
        LocalCommandInterpretation(
            LocalCommandInterpretationStatus.INVALID,
            invalid_reason=LocalCommandInvalidReason.INVALID_INPUT,
        )
    )


def _request(workspace: object = "workspace", text: object = "text"):
    return AuthenticatedLocalCommandRequest(
        LocalAuthenticationProof("proof"),
        workspace,
        text,
        CognitiveFallbackAuthorization(False),
    )


def _service(authentication=None, mapping=None, membership=None, routed=None):
    authenticator, mapper, membership_service, router = (Mock() for _ in range(4))
    authenticator.authenticate.return_value = authentication or _authentication()
    mapper.map.return_value = mapping or _mapping()
    membership_service.decide.return_value = membership or _membership()
    router.route.return_value = routed or _text_result()
    service = AuthenticatedLocalCommandRoutingService(
        authenticator, mapper, membership_service, router
    )
    return service, authenticator, mapper, membership_service, router


def test_request_has_exact_immutable_shape_and_defers_opaque_inputs() -> None:
    proof = LocalAuthenticationProof("proof")
    fallback = CognitiveFallbackAuthorization(False)
    request = AuthenticatedLocalCommandRequest(proof, object(), object(), fallback)
    assert tuple(field.name for field in fields(request)) == (
        "authentication_proof",
        "requested_workspace_id",
        "text",
        "fallback_authorization",
    )
    assert request.authentication_proof is proof
    with pytest.raises(FrozenInstanceError):
        request.text = "other"
    assert not hasattr(request, "__dict__")


@pytest.mark.parametrize(
    "values",
    (
        (object(), CognitiveFallbackAuthorization(False)),
        (LocalAuthenticationProof("proof"), object()),
    ),
)
def test_request_rejects_invalid_typed_inputs(values) -> None:
    with pytest.raises(ValueError):
        AuthenticatedLocalCommandRequest(values[0], object(), object(), values[1])


def test_workspace_selection_result_accepts_only_closed_states() -> None:
    workspace = WorkspaceIdentity("workspace")
    assert AuthenticatedWorkspaceSelectionResult(True, workspace).workspace is workspace
    failure = _selection(False)
    assert failure.error_code is (
        AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
    )
    invalid = (
        {"success": 1, "workspace": workspace},
        {"success": True},
        {"success": True, "workspace": workspace, "error_code": failure.error_code},
        {"success": False, "workspace": workspace, "error_code": failure.error_code},
        {"success": False},
        {"success": False, "error_code": "workspace_selection_invalid"},
    )
    for values in invalid:
        with pytest.raises(ValueError):
            AuthenticatedWorkspaceSelectionResult(**values)


def test_routing_result_accepts_each_terminal_stage() -> None:
    authentication, mapping, selection = _authentication(), _mapping(), _selection()
    decision, routed = _membership(), _text_result()
    auth_failure = AuthenticatedLocalCommandRoutingResult(_authentication(False))
    mapping_failure = AuthenticatedLocalCommandRoutingResult(
        authentication, _mapping(False)
    )
    workspace_failure = AuthenticatedLocalCommandRoutingResult(
        authentication, mapping, _selection(False)
    )
    membership_failure = AuthenticatedLocalCommandRoutingResult(
        authentication, mapping, selection, _membership(False)
    )
    completed = AuthenticatedLocalCommandRoutingResult(
        authentication, mapping, selection, decision, routed
    )
    assert not auth_failure.authentication_result.success
    assert not mapping_failure.mapping_result.success
    assert not workspace_failure.workspace_selection_result.success
    assert not membership_failure.membership_decision.success
    assert completed.text_routing_result is routed


def test_routing_result_rejects_out_of_order_or_missing_states() -> None:
    auth_ok, auth_fail = _authentication(), _authentication(False)
    map_ok, map_fail = _mapping(), _mapping(False)
    selection_ok, selection_fail = _selection(), _selection(False)
    member_ok, member_fail, routed = _membership(), _membership(False), _text_result()
    invalid = (
        (auth_fail, map_fail),
        (auth_ok,),
        (auth_ok, map_fail, selection_fail),
        (auth_ok, map_ok),
        (auth_ok, map_ok, selection_fail, member_fail),
        (auth_ok, map_ok, selection_ok),
        (auth_ok, map_ok, selection_ok, member_fail, routed),
        (auth_ok, map_ok, selection_ok, member_ok),
    )
    for values in invalid:
        with pytest.raises(ValueError):
            AuthenticatedLocalCommandRoutingResult(*values)


def test_routing_result_rejects_mismatched_successful_membership() -> None:
    with pytest.raises(ValueError, match="inconsistent"):
        AuthenticatedLocalCommandRoutingResult(
            _authentication(),
            _mapping(),
            _selection(),
            _membership(actor=ActorIdentity("wrong")),
            _text_result(),
        )


def test_authentication_failure_precedes_workspace_inspection() -> None:
    service, authenticator, mapper, membership, router = _service(
        authentication=_authentication(False)
    )
    result = service.route(_request(object()))
    authenticator.authenticate.assert_called_once()
    mapper.map.assert_not_called()
    membership.decide.assert_not_called()
    router.route.assert_not_called()
    assert not result.authentication_result.success
    assert result.workspace_selection_result is None


def test_mapping_failure_precedes_workspace_inspection() -> None:
    service, authenticator, mapper, membership, router = _service(
        mapping=_mapping(False)
    )
    result = service.route(_request(object()))
    authenticator.authenticate.assert_called_once()
    mapper.map.assert_called_once_with(PrincipalIdentity("principal"))
    membership.decide.assert_not_called()
    router.route.assert_not_called()
    assert not result.mapping_result.success


def test_invalid_workspace_is_controlled_after_authentication_and_mapping() -> None:
    service, authenticator, mapper, membership, router = _service()
    result = service.route(_request(object()))
    authenticator.authenticate.assert_called_once()
    mapper.map.assert_called_once()
    membership.decide.assert_not_called()
    router.route.assert_not_called()
    assert result.workspace_selection_result.error_code is (
        AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
    )


@pytest.mark.parametrize(
    "error", (MEMBERSHIP_NOT_FOUND, MEMBERSHIP_INACTIVE, MEMBERSHIP_RESOLUTION_FAILED)
)
def test_membership_failures_are_terminal(error) -> None:
    service, _, _, membership, router = _service(
        membership=_membership(False, error=error)
    )
    result = service.route(_request())
    membership.decide.assert_called_once_with(
        ActorIdentity("actor"), WorkspaceIdentity("workspace")
    )
    router.route.assert_not_called()
    assert result.membership_decision.error_code == error


def test_success_preserves_order_normalization_and_safe_text_request() -> None:
    calls = []
    service, authenticator, mapper, membership, router = _service()
    authenticator.authenticate.side_effect = lambda proof: (
        calls.append("authenticate") or _authentication()
    )
    mapper.map.side_effect = lambda principal: calls.append("map") or _mapping()
    membership.decide.side_effect = lambda actor, workspace: (
        calls.append("membership") or _membership(workspace=workspace)
    )
    routed_result = _text_result()
    router.route.side_effect = lambda request: calls.append("route") or routed_result
    text, fallback = object(), CognitiveFallbackAuthorization(True)
    result = service.route(
        AuthenticatedLocalCommandRequest(
            LocalAuthenticationProof("proof"), "  Workspace-A  ", text, fallback
        )
    )
    assert calls == ["authenticate", "map", "membership", "route"]
    routed_request = router.route.call_args.args[0]
    assert routed_request.actor == ActorIdentity("actor")
    assert routed_request.workspace == WorkspaceIdentity("Workspace-A")
    assert routed_request.text is text
    assert routed_request.fallback_authorization is fallback
    assert not hasattr(routed_request, "principal")
    assert not hasattr(routed_request, "authentication_proof")
    assert result.text_routing_result is routed_result


@pytest.mark.parametrize("mismatch", ("actor", "workspace"))
def test_membership_identity_mismatch_raises_before_routing(mismatch) -> None:
    actor = ActorIdentity("wrong") if mismatch == "actor" else ActorIdentity("actor")
    workspace = (
        WorkspaceIdentity("wrong")
        if mismatch == "workspace"
        else WorkspaceIdentity("workspace")
    )
    service, _, _, _, router = _service(
        membership=_membership(actor=actor, workspace=workspace)
    )
    with pytest.raises(TypeError, match="inconsistent"):
        service.route(_request())
    router.route.assert_not_called()


@pytest.mark.parametrize("stage", ("authenticator", "mapper", "membership", "router"))
def test_malformed_collaborator_output_raises_type_error(stage) -> None:
    service, authenticator, mapper, membership, router = _service()
    collaborator = {
        "authenticator": authenticator.authenticate,
        "mapper": mapper.map,
        "membership": membership.decide,
        "router": router.route,
    }[stage]
    collaborator.return_value = object()
    with pytest.raises(TypeError):
        service.route(_request())
    if stage == "authenticator":
        mapper.map.assert_not_called()
    if stage in ("authenticator", "mapper"):
        membership.decide.assert_not_called()
    if stage != "router":
        router.route.assert_not_called()


@pytest.mark.parametrize("stage", ("authenticator", "mapper", "membership", "router"))
def test_unexpected_collaborator_errors_propagate(stage) -> None:
    service, authenticator, mapper, membership, router = _service()
    {
        "authenticator": authenticator.authenticate,
        "mapper": mapper.map,
        "membership": membership.decide,
        "router": router.route,
    }[stage].side_effect = RuntimeError(stage)
    with pytest.raises(RuntimeError, match=stage):
        service.route(_request())


def test_service_requires_exact_request_and_non_none_dependencies() -> None:
    service, authenticator, mapper, membership, router = _service()
    with pytest.raises(TypeError):
        service.route(object())
    dependencies = [authenticator, mapper, membership, router]
    for index in range(4):
        values = dependencies.copy()
        values[index] = None
        with pytest.raises(ValueError):
            AuthenticatedLocalCommandRoutingService(*values)
