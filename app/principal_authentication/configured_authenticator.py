"""Deterministic non-production local principal authenticators."""

from dataclasses import dataclass, field
from hmac import compare_digest
from types import MappingProxyType

from app.principal_authentication.models import (
    AuthenticatedPrincipal,
    LocalAuthenticationProof,
    PrincipalAuthenticationErrorCode,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)


@dataclass(frozen=True, slots=True)
class ConfiguredPrincipalProofBinding:
    """Process-local demo verifier material; not production authentication."""

    principal: PrincipalIdentity
    verifier_value: str = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.principal) is not PrincipalIdentity:
            raise ValueError("Configured principal identity is invalid.")
        if not isinstance(self.verifier_value, str) or not self.verifier_value:
            raise ValueError("Verifier value must be a non-empty string.")


class RejectingLocalPrincipalAuthenticator:
    def authenticate(
        self, proof: LocalAuthenticationProof
    ) -> PrincipalAuthenticationResult:
        if type(proof) is not LocalAuthenticationProof:
            raise TypeError("A valid local authentication proof is required.")
        return PrincipalAuthenticationResult(
            False,
            error_code=PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
        )


class ConfiguredLocalPrincipalAuthenticator:
    """Deterministic process-local development/test/demo authenticator only."""

    __slots__ = ("_principals_by_verifier",)

    def __init__(
        self, bindings: tuple[ConfiguredPrincipalProofBinding, ...] = ()
    ) -> None:
        if type(bindings) is not tuple:
            raise ValueError("Configured proof bindings must be a tuple.")
        principals_by_verifier: dict[str, PrincipalIdentity] = {}
        configured_principals: set[PrincipalIdentity] = set()
        for binding in tuple(bindings):
            if type(binding) is not ConfiguredPrincipalProofBinding:
                raise ValueError("Configured proof binding is invalid.")
            if binding.verifier_value in principals_by_verifier:
                raise ValueError("Configured verifier values must be unique.")
            if binding.principal in configured_principals:
                raise ValueError("Configured principal identities must be unique.")
            principals_by_verifier[binding.verifier_value] = binding.principal
            configured_principals.add(binding.principal)
        self._principals_by_verifier = MappingProxyType(principals_by_verifier)

    def authenticate(
        self, proof: LocalAuthenticationProof
    ) -> PrincipalAuthenticationResult:
        if type(proof) is not LocalAuthenticationProof:
            raise TypeError("A valid local authentication proof is required.")
        if not isinstance(proof.proof, str) or not proof.proof:
            return self._failed()
        matched_principal = None
        for verifier_value, principal in self._principals_by_verifier.items():
            if compare_digest(proof.proof, verifier_value):
                matched_principal = principal
        if matched_principal is None:
            return self._failed()
        return PrincipalAuthenticationResult(
            True,
            AuthenticatedPrincipal(matched_principal),
        )

    @staticmethod
    def _failed() -> PrincipalAuthenticationResult:
        return PrincipalAuthenticationResult(
            False,
            error_code=PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
        )
