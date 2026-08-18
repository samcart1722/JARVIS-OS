import pytest

from app.cognition.local_resolution.models import ActorIdentity
from app.principal_authentication.configured_mapper import (
    ConfiguredPrincipalActorMapper,
    ConfiguredPrincipalActorMapping,
)
from app.principal_authentication.models import (
    PrincipalActorMappingErrorCode,
    PrincipalIdentity,
)


def _mapping(principal_id: str = "principal", actor_id: str = "actor"):
    return ConfiguredPrincipalActorMapping(
        PrincipalIdentity(principal_id), ActorIdentity(actor_id)
    )


def test_exact_mapping_returns_the_configured_actor() -> None:
    mapping = _mapping()
    result = ConfiguredPrincipalActorMapper((mapping,)).map(mapping.principal)
    assert result.success
    assert result.actor is mapping.actor
    assert result.error_code is None


def test_mapping_is_case_sensitive_and_missing_collapses_to_stable_failure() -> None:
    mapper = ConfiguredPrincipalActorMapper((_mapping("Principal"),))
    result = mapper.map(PrincipalIdentity("principal"))
    assert not result.success
    assert result.actor is None
    assert result.error_code is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED


def test_duplicate_principal_mapping_is_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        ConfiguredPrincipalActorMapper(
            (_mapping("same", "one"), _mapping("same", "two"))
        )


def test_multiple_principals_may_map_to_the_same_actor() -> None:
    mapper = ConfiguredPrincipalActorMapper(
        (_mapping("one", "shared"), _mapping("two", "shared"))
    )
    first = mapper.map(PrincipalIdentity("one"))
    second = mapper.map(PrincipalIdentity("two"))
    assert first.success and second.success
    assert first.actor == second.actor == ActorIdentity("shared")


def test_mapper_configuration_is_a_defensive_immutable_copy() -> None:
    configured = [_mapping()]
    mapper = ConfiguredPrincipalActorMapper(tuple(configured))
    configured.clear()
    assert mapper.map(PrincipalIdentity("principal")).success
    with pytest.raises(TypeError):
        mapper._actors_by_principal[PrincipalIdentity("new")] = ActorIdentity("new")


def test_mapping_validates_exact_inputs() -> None:
    with pytest.raises(ValueError):
        ConfiguredPrincipalActorMapping(object(), ActorIdentity("actor"))
    with pytest.raises(ValueError):
        ConfiguredPrincipalActorMapping(PrincipalIdentity("principal"), object())
    with pytest.raises(TypeError):
        ConfiguredPrincipalActorMapper().map(object())


@pytest.mark.parametrize("value", ([], "", b"", object()))
def test_mapper_requires_tuple_configuration(value) -> None:
    with pytest.raises(ValueError):
        ConfiguredPrincipalActorMapper(value)


def test_mapper_rejects_invalid_mapping() -> None:
    with pytest.raises(ValueError):
        ConfiguredPrincipalActorMapper((object(),))
