from dataclasses import FrozenInstanceError, fields

import pytest

from app.cognition.local_resolution.models import ActorIdentity
from app.principal_authentication.models import (
    AuthenticatedPrincipal,
    LocalAuthenticationProof,
    PrincipalActorMappingErrorCode,
    PrincipalActorMappingResult,
    PrincipalAuthenticationErrorCode,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)


def test_principal_identity_normalizes_only_surrounding_whitespace() -> None:
    principal = PrincipalIdentity("  Principal  One  ")
    assert principal.principal_id == "Principal  One"


def test_principal_identity_equality_and_hash_are_case_sensitive() -> None:
    upper = PrincipalIdentity("Principal")
    lower = PrincipalIdentity("principal")
    assert upper != lower
    assert hash(upper) != hash(lower)


@pytest.mark.parametrize("value", ("", "   ", None, 1, object()))
def test_principal_identity_rejects_invalid_values(value) -> None:
    with pytest.raises(ValueError):
        PrincipalIdentity(value)


def test_principal_identity_is_frozen_and_slotted() -> None:
    principal = PrincipalIdentity("principal")
    with pytest.raises(FrozenInstanceError):
        principal.principal_id = "other"
    assert not hasattr(principal, "__dict__")


def test_local_authentication_proof_is_opaque_frozen_and_not_repr_visible() -> None:
    opaque = object()
    proof = LocalAuthenticationProof(opaque)
    assert proof.proof is opaque
    assert repr(opaque) not in repr(proof)
    with pytest.raises(FrozenInstanceError):
        proof.proof = object()
    assert not hasattr(proof, "__dict__")


def test_authenticated_principal_has_exact_safe_shape() -> None:
    identity = PrincipalIdentity("principal")
    authenticated = AuthenticatedPrincipal(identity)
    assert authenticated.principal is identity
    assert tuple(field.name for field in fields(authenticated)) == ("principal",)
    for name in ("actor", "workspace", "permission", "permissions", "proof"):
        assert not hasattr(authenticated, name)
    with pytest.raises(FrozenInstanceError):
        authenticated.principal = PrincipalIdentity("other")
    assert not hasattr(authenticated, "__dict__")


def test_authenticated_principal_requires_exact_principal_identity() -> None:
    with pytest.raises(ValueError):
        AuthenticatedPrincipal(object())


def test_authentication_result_accepts_only_valid_closed_states() -> None:
    authenticated = AuthenticatedPrincipal(PrincipalIdentity("principal"))
    success = PrincipalAuthenticationResult(True, authenticated)
    failure = PrincipalAuthenticationResult(
        False,
        error_code=PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
    )
    assert success.principal is authenticated and success.error_code is None
    assert not failure.success and failure.principal is None

    invalid = (
        {"success": 1, "principal": authenticated},
        {"success": True},
        {
            "success": True,
            "principal": authenticated,
            "error_code": PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
        },
        {"success": False, "principal": authenticated},
        {"success": False},
        {"success": False, "error_code": "authentication_failed"},
    )
    for values in invalid:
        with pytest.raises(ValueError):
            PrincipalAuthenticationResult(**values)


def test_mapping_result_accepts_only_valid_closed_states() -> None:
    actor = ActorIdentity("actor")
    success = PrincipalActorMappingResult(True, actor)
    failure = PrincipalActorMappingResult(
        False,
        error_code=PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
    )
    assert success.actor is actor and success.error_code is None
    assert not failure.success and failure.actor is None

    invalid = (
        {"success": 1, "actor": actor},
        {"success": True},
        {
            "success": True,
            "actor": actor,
            "error_code": PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
        },
        {"success": False, "actor": actor},
        {"success": False},
        {"success": False, "error_code": "principal_mapping_failed"},
    )
    for values in invalid:
        with pytest.raises(ValueError):
            PrincipalActorMappingResult(**values)


def test_error_sets_are_exact() -> None:
    assert tuple(PrincipalAuthenticationErrorCode) == (
        PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
        PrincipalAuthenticationErrorCode.AUTHENTICATION_RESOLUTION_FAILED,
    )
    assert tuple(PrincipalActorMappingErrorCode) == (
        PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
    )
