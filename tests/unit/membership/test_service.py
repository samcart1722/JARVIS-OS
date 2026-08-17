from unittest.mock import Mock

import pytest

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.membership.contracts import MembershipRepositoryError
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipStatus,
)
from app.membership.service import MembershipDecisionService


def _identities() -> tuple[ActorIdentity, WorkspaceIdentity]:
    return ActorIdentity("actor"), WorkspaceIdentity("workspace")


def _service(result=None, side_effect=None):
    repository = Mock()
    repository.get.return_value = result
    repository.get.side_effect = side_effect
    return MembershipDecisionService(repository), repository


def test_constructor_requires_repository_but_preserves_falsey_collaborator() -> None:
    with pytest.raises(ValueError):
        MembershipDecisionService(None)
    repository = Mock()
    repository.__bool__ = Mock(return_value=False)
    service = MembershipDecisionService(repository)
    assert service._repository is repository


def test_active_membership_succeeds_and_preserves_exact_objects() -> None:
    actor, workspace = _identities()
    membership = ActorWorkspaceMembership(actor, workspace, MembershipStatus.ACTIVE)
    service, repository = _service(membership)

    decision = service.decide(actor, workspace)

    assert decision.success
    assert decision.membership is membership
    assert decision.error_code is None
    repository.get.assert_called_once_with(actor, workspace)


@pytest.mark.parametrize(
    ("repository_result", "error_code"),
    (
        (None, MEMBERSHIP_NOT_FOUND),
        (
            ActorWorkspaceMembership(
                ActorIdentity("actor"),
                WorkspaceIdentity("workspace"),
                MembershipStatus.INACTIVE,
            ),
            MEMBERSHIP_INACTIVE,
        ),
        (object(), MEMBERSHIP_RESOLUTION_FAILED),
    ),
)
def test_missing_inactive_and_malformed_results_fail_safely(
    repository_result, error_code
) -> None:
    actor, workspace = _identities()
    service, repository = _service(repository_result)

    decision = service.decide(actor, workspace)

    assert not decision.success
    assert decision.membership is None
    assert decision.error_code == error_code
    repository.get.assert_called_once_with(actor, workspace)


def test_repository_failure_maps_to_safe_code_without_leaking_detail() -> None:
    actor, workspace = _identities()
    service, repository = _service(
        side_effect=MembershipRepositoryError("sensitive storage detail")
    )

    decision = service.decide(actor, workspace)

    assert decision.error_code == MEMBERSHIP_RESOLUTION_FAILED
    assert "sensitive" not in decision.error_code
    repository.get.assert_called_once_with(actor, workspace)


@pytest.mark.parametrize(
    ("actor", "workspace"),
    (
        (object(), WorkspaceIdentity("workspace")),
        (ActorIdentity("actor"), object()),
    ),
)
def test_exact_identity_types_are_required_before_repository_access(
    actor, workspace
) -> None:
    service, repository = _service()
    with pytest.raises(ValueError):
        service.decide(actor, workspace)
    repository.get.assert_not_called()


def test_decision_never_calls_lifecycle_mutations() -> None:
    actor, workspace = _identities()
    membership = ActorWorkspaceMembership(actor, workspace, MembershipStatus.ACTIVE)
    service, repository = _service(membership)

    service.decide(actor, workspace)

    repository.create.assert_not_called()
    repository.activate.assert_not_called()
    repository.deactivate.assert_not_called()
