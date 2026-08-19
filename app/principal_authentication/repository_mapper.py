"""Principal-to-actor mapping backed by an injected repository."""

from app.cognition.local_resolution.models import ActorIdentity
from app.principal_authentication.contracts import (
    PrincipalActorMappingRepository,
    PrincipalActorMappingRepositoryError,
)
from app.principal_authentication.models import (
    PrincipalActorMappingErrorCode,
    PrincipalActorMappingResult,
    PrincipalIdentity,
)


class RepositoryPrincipalActorMapper:
    """Resolve principal identities through one injected repository."""

    __slots__ = ("_repository",)

    def __init__(self, repository: PrincipalActorMappingRepository) -> None:
        if repository is None:
            raise ValueError("A principal actor mapping repository is required.")
        self._repository = repository

    def map(self, principal: PrincipalIdentity) -> PrincipalActorMappingResult:
        if type(principal) is not PrincipalIdentity:
            raise TypeError("A valid principal identity is required.")

        try:
            actor = self._repository.get(principal)
        except PrincipalActorMappingRepositoryError:
            return PrincipalActorMappingResult(
                False,
                error_code=(
                    PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
                ),
            )

        if actor is None:
            return PrincipalActorMappingResult(
                False,
                error_code=PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
            )

        if type(actor) is not ActorIdentity:
            return PrincipalActorMappingResult(
                False,
                error_code=(
                    PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
                ),
            )

        return PrincipalActorMappingResult(True, actor)
