"""Deterministic configured principal-to-actor mapping."""

from dataclasses import dataclass
from types import MappingProxyType

from app.cognition.local_resolution.models import ActorIdentity
from app.principal_authentication.models import (
    PrincipalActorMappingErrorCode,
    PrincipalActorMappingResult,
    PrincipalIdentity,
)


@dataclass(frozen=True, slots=True)
class ConfiguredPrincipalActorMapping:
    principal: PrincipalIdentity
    actor: ActorIdentity

    def __post_init__(self) -> None:
        if type(self.principal) is not PrincipalIdentity:
            raise ValueError("Configured principal identity is invalid.")
        if type(self.actor) is not ActorIdentity:
            raise ValueError("Configured actor identity is invalid.")


class ConfiguredPrincipalActorMapper:
    __slots__ = ("_actors_by_principal",)

    def __init__(
        self, mappings: tuple[ConfiguredPrincipalActorMapping, ...] = ()
    ) -> None:
        if type(mappings) is not tuple:
            raise ValueError("Configured principal mappings must be a tuple.")
        actors_by_principal: dict[PrincipalIdentity, ActorIdentity] = {}
        for mapping in tuple(mappings):
            if type(mapping) is not ConfiguredPrincipalActorMapping:
                raise ValueError("Configured principal mapping is invalid.")
            if mapping.principal in actors_by_principal:
                raise ValueError("Configured principal mappings must be unique.")
            actors_by_principal[mapping.principal] = mapping.actor
        self._actors_by_principal = MappingProxyType(actors_by_principal)

    def map(self, principal: PrincipalIdentity) -> PrincipalActorMappingResult:
        if type(principal) is not PrincipalIdentity:
            raise TypeError("A valid principal identity is required.")
        actor = self._actors_by_principal.get(principal)
        if actor is None:
            return PrincipalActorMappingResult(
                False,
                error_code=(
                    PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED
                ),
            )
        return PrincipalActorMappingResult(True, actor)
