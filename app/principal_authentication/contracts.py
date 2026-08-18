"""Infrastructure-free local principal authentication contracts."""

from typing import Protocol

from app.principal_authentication.models import (
    LocalAuthenticationProof,
    PrincipalActorMappingResult,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)


class LocalPrincipalAuthenticator(Protocol):
    def authenticate(
        self, proof: LocalAuthenticationProof
    ) -> PrincipalAuthenticationResult: ...


class PrincipalActorMapper(Protocol):
    def map(self, principal: PrincipalIdentity) -> PrincipalActorMappingResult: ...
