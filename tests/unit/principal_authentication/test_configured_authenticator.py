from unittest.mock import patch

import pytest

from app.principal_authentication.configured_authenticator import (
    ConfiguredLocalPrincipalAuthenticator,
    ConfiguredPrincipalProofBinding,
    RejectingLocalPrincipalAuthenticator,
)
from app.principal_authentication.models import (
    LocalAuthenticationProof,
    PrincipalAuthenticationErrorCode,
    PrincipalIdentity,
)


def _binding(principal_id: str = "principal", verifier: str = "Exact Proof"):
    return ConfiguredPrincipalProofBinding(
        PrincipalIdentity(principal_id), verifier
    )


def test_rejecting_authenticator_is_deterministically_fail_closed() -> None:
    authenticator = RejectingLocalPrincipalAuthenticator()
    first = authenticator.authenticate(LocalAuthenticationProof("anything"))
    second = authenticator.authenticate(LocalAuthenticationProof(object()))
    assert first == second
    assert first.error_code is PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED


def test_authenticators_reject_programming_misuse() -> None:
    with pytest.raises(TypeError):
        RejectingLocalPrincipalAuthenticator().authenticate(object())
    with pytest.raises(TypeError):
        ConfiguredLocalPrincipalAuthenticator().authenticate(object())


def test_exact_proof_authenticates_the_configured_principal() -> None:
    principal = PrincipalIdentity("principal")
    authenticator = ConfiguredLocalPrincipalAuthenticator(
        (ConfiguredPrincipalProofBinding(principal, " exact "),)
    )
    result = authenticator.authenticate(LocalAuthenticationProof(" exact "))
    assert result.success
    assert result.principal.principal is principal
    assert result.error_code is None


@pytest.mark.parametrize(
    "proof", ("unknown", "Exact Proof ", "exact proof", "", None, 7, object())
)
def test_unknown_wrong_or_malformed_proof_has_one_failure(proof) -> None:
    result = ConfiguredLocalPrincipalAuthenticator((_binding(),)).authenticate(
        LocalAuthenticationProof(proof)
    )
    assert not result.success
    assert result.principal is None
    assert result.error_code is PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED


def test_verifier_comparison_uses_compare_digest() -> None:
    authenticator = ConfiguredLocalPrincipalAuthenticator(
        (_binding("one", "first"), _binding("two", "second"))
    )
    with patch(
        "app.principal_authentication.configured_authenticator.compare_digest",
        wraps=__import__("hmac").compare_digest,
    ) as compare:
        result = authenticator.authenticate(LocalAuthenticationProof("second"))
    assert result.success
    assert compare.call_count == 2


@pytest.mark.parametrize("value", ("", None, 1, object()))
def test_proof_binding_rejects_invalid_verifier_values(value) -> None:
    with pytest.raises(ValueError):
        ConfiguredPrincipalProofBinding(PrincipalIdentity("principal"), value)


def test_proof_binding_requires_exact_principal() -> None:
    with pytest.raises(ValueError):
        ConfiguredPrincipalProofBinding(object(), "proof")


def test_duplicate_verifier_and_ambiguous_principal_are_rejected() -> None:
    with pytest.raises(ValueError, match="verifier"):
        ConfiguredLocalPrincipalAuthenticator(
            (_binding("one", "same"), _binding("two", "same"))
        )
    with pytest.raises(ValueError, match="principal"):
        ConfiguredLocalPrincipalAuthenticator(
            (_binding("same", "one"), _binding("same", "two"))
        )


def test_configuration_is_a_defensive_immutable_copy() -> None:
    configured = [_binding()]
    authenticator = ConfiguredLocalPrincipalAuthenticator(tuple(configured))
    configured.clear()
    assert authenticator.authenticate(LocalAuthenticationProof("Exact Proof")).success
    with pytest.raises(TypeError):
        authenticator._principals_by_verifier["new"] = PrincipalIdentity("new")


def test_proof_and_verifier_are_not_exposed_by_results_or_repr() -> None:
    secret = "private-demo-verifier"
    binding = _binding(verifier=secret)
    authenticator = ConfiguredLocalPrincipalAuthenticator((binding,))
    result = authenticator.authenticate(LocalAuthenticationProof(secret))
    assert secret not in repr(binding)
    assert secret not in repr(result)
    assert not hasattr(result, "proof")
    assert not hasattr(result.principal, "proof")


def test_configured_authentication_is_deterministic() -> None:
    authenticator = ConfiguredLocalPrincipalAuthenticator((_binding(),))
    proof = LocalAuthenticationProof("Exact Proof")
    assert authenticator.authenticate(proof) == authenticator.authenticate(proof)


@pytest.mark.parametrize("value", ([], "", b"", object()))
def test_authenticator_requires_tuple_configuration(value) -> None:
    with pytest.raises(ValueError):
        ConfiguredLocalPrincipalAuthenticator(value)


def test_authenticator_rejects_invalid_binding() -> None:
    with pytest.raises(ValueError):
        ConfiguredLocalPrincipalAuthenticator((object(),))
