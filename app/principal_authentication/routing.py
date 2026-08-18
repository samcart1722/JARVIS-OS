"""Authentication-first orchestration for local command routing."""

from dataclasses import dataclass
from enum import Enum

from app.cognition.interpretation.routing import (
    LocalCommandTextRouter,
    TextRoutingRequest,
    TextRoutingResult,
)
from app.cognition.local_resolution.models import WorkspaceIdentity
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.membership.models import MembershipDecision
from app.membership.service import MembershipDecisionService
from app.principal_authentication.contracts import (
    LocalPrincipalAuthenticator,
    PrincipalActorMapper,
)
from app.principal_authentication.models import (
    LocalAuthenticationProof,
    PrincipalActorMappingResult,
    PrincipalAuthenticationResult,
)


@dataclass(frozen=True, slots=True)
class AuthenticatedLocalCommandRequest:
    authentication_proof: LocalAuthenticationProof
    requested_workspace_id: object
    text: object
    fallback_authorization: CognitiveFallbackAuthorization

    def __post_init__(self) -> None:
        if type(self.authentication_proof) is not LocalAuthenticationProof:
            raise ValueError("A valid local authentication proof is required.")
        if type(self.fallback_authorization) is not CognitiveFallbackAuthorization:
            raise ValueError("Explicit fallback authorization is required.")


class AuthenticatedWorkspaceSelectionErrorCode(str, Enum):
    WORKSPACE_SELECTION_INVALID = "workspace_selection_invalid"


@dataclass(frozen=True, slots=True)
class AuthenticatedWorkspaceSelectionResult:
    success: bool
    workspace: WorkspaceIdentity | None = None
    error_code: AuthenticatedWorkspaceSelectionErrorCode | None = None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise ValueError("Workspace selection success must be explicit.")
        if self.success:
            if type(self.workspace) is not WorkspaceIdentity:
                raise ValueError("Successful selection requires a workspace.")
            if self.error_code is not None:
                raise ValueError("Successful selection forbids an error.")
            return
        if self.workspace is not None:
            raise ValueError("Failed selection forbids a workspace.")
        if (
            self.error_code
            is not AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
        ):
            raise ValueError("Failed selection requires the valid error.")


@dataclass(frozen=True, slots=True)
class AuthenticatedLocalCommandRoutingResult:
    authentication_result: PrincipalAuthenticationResult
    mapping_result: PrincipalActorMappingResult | None = None
    workspace_selection_result: AuthenticatedWorkspaceSelectionResult | None = None
    membership_decision: MembershipDecision | None = None
    text_routing_result: TextRoutingResult | None = None

    def __post_init__(self) -> None:
        authentication = self.authentication_result
        if type(authentication) is not PrincipalAuthenticationResult:
            raise ValueError("A valid authentication result is required.")
        if not authentication.success:
            self._forbid_downstream("authentication failure")
            return

        mapping = self.mapping_result
        if type(mapping) is not PrincipalActorMappingResult:
            raise ValueError("Authentication success requires a mapping result.")
        if not mapping.success:
            if any(
                value is not None
                for value in (
                    self.workspace_selection_result,
                    self.membership_decision,
                    self.text_routing_result,
                )
            ):
                raise ValueError("Mapping failure forbids downstream results.")
            return

        selection = self.workspace_selection_result
        if type(selection) is not AuthenticatedWorkspaceSelectionResult:
            raise ValueError("Mapping success requires workspace selection.")
        if not selection.success:
            if (
                self.membership_decision is not None
                or self.text_routing_result is not None
            ):
                raise ValueError("Workspace failure forbids downstream results.")
            return

        decision = self.membership_decision
        if type(decision) is not MembershipDecision:
            raise ValueError("Workspace success requires a membership decision.")
        if not decision.success:
            if self.text_routing_result is not None:
                raise ValueError("Membership failure forbids text routing.")
            return
        if (
            decision.membership.actor != mapping.actor
            or decision.membership.workspace != selection.workspace
        ):
            raise ValueError("Successful membership identity is inconsistent.")
        if type(self.text_routing_result) is not TextRoutingResult:
            raise ValueError("Membership success requires a text-routing result.")

    def _forbid_downstream(self, stage: str) -> None:
        if any(
            value is not None
            for value in (
                self.mapping_result,
                self.workspace_selection_result,
                self.membership_decision,
                self.text_routing_result,
            )
        ):
            raise ValueError(f"{stage.capitalize()} forbids downstream results.")


class AuthenticatedLocalCommandRoutingService:
    __slots__ = ("_authenticator", "_mapper", "_membership_service", "_router")

    def __init__(
        self,
        authenticator: LocalPrincipalAuthenticator,
        mapper: PrincipalActorMapper,
        membership_service: MembershipDecisionService,
        router: LocalCommandTextRouter,
    ) -> None:
        if authenticator is None:
            raise ValueError("An authenticator is required.")
        if mapper is None:
            raise ValueError("A principal mapper is required.")
        if membership_service is None:
            raise ValueError("A membership service is required.")
        if router is None:
            raise ValueError("A text router is required.")
        self._authenticator = authenticator
        self._mapper = mapper
        self._membership_service = membership_service
        self._router = router

    def route(
        self, request: AuthenticatedLocalCommandRequest
    ) -> AuthenticatedLocalCommandRoutingResult:
        if type(request) is not AuthenticatedLocalCommandRequest:
            raise TypeError("A valid authenticated local command request is required.")

        authentication = self._authenticator.authenticate(
            request.authentication_proof
        )
        if type(authentication) is not PrincipalAuthenticationResult:
            raise TypeError("Authenticator returned an invalid result.")
        if not authentication.success:
            return AuthenticatedLocalCommandRoutingResult(authentication)

        mapping = self._mapper.map(authentication.principal.principal)
        if type(mapping) is not PrincipalActorMappingResult:
            raise TypeError("Principal mapper returned an invalid result.")
        if not mapping.success:
            return AuthenticatedLocalCommandRoutingResult(authentication, mapping)

        try:
            workspace = WorkspaceIdentity(request.requested_workspace_id)
        except ValueError:
            selection = AuthenticatedWorkspaceSelectionResult(
                False,
                error_code=(
                    AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
                ),
            )
            return AuthenticatedLocalCommandRoutingResult(
                authentication, mapping, selection
            )
        selection = AuthenticatedWorkspaceSelectionResult(True, workspace)

        decision = self._membership_service.decide(mapping.actor, workspace)
        if type(decision) is not MembershipDecision:
            raise TypeError("Membership service returned an invalid result.")
        if decision.success and (
            decision.membership.actor != mapping.actor
            or decision.membership.workspace != workspace
        ):
            raise TypeError("Membership service returned inconsistent identity data.")
        if not decision.success:
            return AuthenticatedLocalCommandRoutingResult(
                authentication, mapping, selection, decision
            )

        routed = self._router.route(
            TextRoutingRequest(
                actor=mapping.actor,
                workspace=workspace,
                text=request.text,
                fallback_authorization=request.fallback_authorization,
            )
        )
        if type(routed) is not TextRoutingResult:
            raise TypeError("Text router returned an invalid result.")
        return AuthenticatedLocalCommandRoutingResult(
            authentication, mapping, selection, decision, routed
        )
