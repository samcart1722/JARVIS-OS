"""Immutable values for local principal authentication and actor mapping."""

from dataclasses import dataclass, field
from enum import Enum

from app.cognition.local_resolution.models import ActorIdentity


@dataclass(frozen=True, slots=True)
class PrincipalIdentity:
    principal_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.principal_id, str) or not self.principal_id.strip():
            raise ValueError("Principal ID must be a non-empty string.")
        object.__setattr__(self, "principal_id", self.principal_id.strip())


@dataclass(frozen=True, slots=True)
class LocalAuthenticationProof:
    proof: object = field(repr=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    principal: PrincipalIdentity

    def __post_init__(self) -> None:
        if type(self.principal) is not PrincipalIdentity:
            raise ValueError("Authenticated principal identity is invalid.")


class PrincipalAuthenticationErrorCode(str, Enum):
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHENTICATION_RESOLUTION_FAILED = "authentication_resolution_failed"


@dataclass(frozen=True, slots=True)
class PrincipalAuthenticationResult:
    success: bool
    principal: AuthenticatedPrincipal | None = None
    error_code: PrincipalAuthenticationErrorCode | None = None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise ValueError("Authentication success must be explicit.")
        if self.success:
            if type(self.principal) is not AuthenticatedPrincipal:
                raise ValueError("Successful authentication requires a principal.")
            if self.error_code is not None:
                raise ValueError("Successful authentication forbids an error.")
            return
        if self.principal is not None:
            raise ValueError("Failed authentication forbids a principal.")
        if type(self.error_code) is not PrincipalAuthenticationErrorCode:
            raise ValueError("Failed authentication requires a valid error.")


class PrincipalActorMappingErrorCode(str, Enum):
    PRINCIPAL_MAPPING_FAILED = "principal_mapping_failed"
    PRINCIPAL_MAPPING_RESOLUTION_FAILED = "principal_mapping_resolution_failed"


@dataclass(frozen=True, slots=True)
class PrincipalActorMappingResult:
    success: bool
    actor: ActorIdentity | None = None
    error_code: PrincipalActorMappingErrorCode | None = None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise ValueError("Principal mapping success must be explicit.")
        if self.success:
            if type(self.actor) is not ActorIdentity:
                raise ValueError("Successful principal mapping requires an actor.")
            if self.error_code is not None:
                raise ValueError("Successful principal mapping forbids an error.")
            return
        if self.actor is not None:
            raise ValueError("Failed principal mapping forbids an actor.")
        if type(self.error_code) is not PrincipalActorMappingErrorCode:
            raise ValueError("Failed principal mapping requires a valid error.")
