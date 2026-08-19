import pytest

from app.cognition.local_resolution.models import ActorIdentity
from app.principal_authentication.contracts import (
    PrincipalActorMappingRepositoryError,
)
from app.principal_authentication.models import (
    PrincipalActorMappingErrorCode,
    PrincipalIdentity,
)
from app.principal_authentication.repository_mapper import (
    RepositoryPrincipalActorMapper,
)


class _Repository:
    def __init__(self, records=None) -> None:
        self.records = {} if records is None else dict(records)
        self.calls = 0

    def get(self, principal):
        self.calls += 1
        return self.records.get(principal.principal_id)

    def create(self, principal, actor):
        raise AssertionError("create must not be called by the mapper")


class _FailingRepository:
    def get(self, principal):
        raise PrincipalActorMappingRepositoryError("unavailable")

    def create(self, principal, actor):
        raise AssertionError("create must not be called by the mapper")


class _ProgrammingFailureRepository:
    def get(self, principal):
        raise RuntimeError("programming failure")

    def create(self, principal, actor):
        raise AssertionError("create must not be called by the mapper")


def test_repository_mapper_returns_exact_actor_once() -> None:
    actor = ActorIdentity("actor")
    repository = _Repository({"Principal": actor})
    result = RepositoryPrincipalActorMapper(repository).map(
        PrincipalIdentity("Principal")
    )

    assert result.success
    assert result.actor is actor
    assert result.error_code is None
    assert repository.calls == 1


def test_repository_mapper_is_case_sensitive_and_missing_fails_closed() -> None:
    repository = _Repository({"Principal": ActorIdentity("actor")})
    result = RepositoryPrincipalActorMapper(repository).map(
        PrincipalIdentity("principal")
    )

    assert not result.success
    assert result.actor is None
    assert result.error_code is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED
    assert repository.calls == 1


def test_repository_failure_becomes_stable_resolution_failure() -> None:
    result = RepositoryPrincipalActorMapper(_FailingRepository()).map(
        PrincipalIdentity("principal")
    )

    assert not result.success
    assert result.actor is None
    assert (
        result.error_code
        is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
    )


def test_invalid_repository_data_becomes_stable_resolution_failure() -> None:
    repository = _Repository({"principal": object()})
    result = RepositoryPrincipalActorMapper(repository).map(
        PrincipalIdentity("principal")
    )

    assert not result.success
    assert result.actor is None
    assert (
        result.error_code
        is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
    )


def test_unexpected_programming_failure_propagates() -> None:
    mapper = RepositoryPrincipalActorMapper(_ProgrammingFailureRepository())

    with pytest.raises(RuntimeError, match="programming failure"):
        mapper.map(PrincipalIdentity("principal"))


def test_repository_mapper_requires_repository() -> None:
    with pytest.raises(ValueError, match="repository"):
        RepositoryPrincipalActorMapper(None)


def test_repository_mapper_requires_exact_principal_identity() -> None:
    repository = _Repository()
    mapper = RepositoryPrincipalActorMapper(repository)

    with pytest.raises(TypeError):
        mapper.map(object())

    assert repository.calls == 0
