"""Local authenticated-principal contracts and deterministic adapters."""

from app.principal_authentication.configured_authenticator import (
    ConfiguredLocalPrincipalAuthenticator,
    ConfiguredPrincipalProofBinding,
    RejectingLocalPrincipalAuthenticator,
)
from app.principal_authentication.configured_mapper import (
    ConfiguredPrincipalActorMapper,
    ConfiguredPrincipalActorMapping,
)
from app.principal_authentication.contracts import (
    LocalPrincipalAuthenticator,
    PrincipalActorMapper,
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
    AuthenticatedLocalCommandRoutingService,
    AuthenticatedWorkspaceSelectionErrorCode,
    AuthenticatedWorkspaceSelectionResult,
)

__all__ = [
    "AuthenticatedPrincipal",
    "AuthenticatedLocalCommandRequest",
    "AuthenticatedLocalCommandRoutingResult",
    "AuthenticatedLocalCommandRoutingService",
    "AuthenticatedWorkspaceSelectionErrorCode",
    "AuthenticatedWorkspaceSelectionResult",
    "ConfiguredLocalPrincipalAuthenticator",
    "ConfiguredPrincipalActorMapper",
    "ConfiguredPrincipalActorMapping",
    "ConfiguredPrincipalProofBinding",
    "LocalAuthenticationProof",
    "LocalPrincipalAuthenticator",
    "PrincipalActorMapper",
    "PrincipalActorMappingErrorCode",
    "PrincipalActorMappingResult",
    "PrincipalAuthenticationErrorCode",
    "PrincipalAuthenticationResult",
    "PrincipalIdentity",
    "RejectingLocalPrincipalAuthenticator",
]
