"""Infrastructure-free local principal authentication contracts."""

from typing import Protocol

from app.cognition.local_resolution.models import ActorIdentity
from app.principal_authentication.models import (
    LocalAuthenticationProof,
    PrincipalActorMappingResult,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)


class PrincipalActorMappingRepositoryError(RuntimeError):
    """Signal a safe principal-actor mapping repository failure."""


class PrincipalActorMappingConflict(PrincipalActorMappingRepositoryError):
    """Signal an attempted duplicate principal mapping."""


class LocalPrincipalAuthenticator(Protocol):
    def authenticate(
        self, proof: LocalAuthenticationProof
    ) -> PrincipalAuthenticationResult: ...


class PrincipalActorMapper(Protocol):
    def map(self, principal: PrincipalIdentity) -> PrincipalActorMappingResult: ...


class PrincipalActorMappingRepository(Protocol):
    def get(self, principal: PrincipalIdentity) -> ActorIdentity | None: ...

    def create(
        self,
        principal: PrincipalIdentity,
        actor: ActorIdentity,
    ) -> ActorIdentity: ...
