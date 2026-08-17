from dataclasses import FrozenInstanceError

import pytest

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.membership.contracts import MembershipRepository
from app.membership.in_memory_repository import InMemoryMembershipRepository
from app.membership.models import ActorWorkspaceMembership, MembershipStatus


def _actor(value: str = "actor") -> ActorIdentity:
    return ActorIdentity(value)


def _workspace(value: str = "workspace") -> WorkspaceIdentity:
    return WorkspaceIdentity(value)


def _membership(
    actor: ActorIdentity | None = None,
    workspace: WorkspaceIdentity | None = None,
    status: MembershipStatus = MembershipStatus.ACTIVE,
) -> ActorWorkspaceMembership:
    return ActorWorkspaceMembership(
        actor or _actor(),
        workspace or _workspace(),
        status,
    )


def test_repository_satisfies_membership_protocol_shape() -> None:
    repository: MembershipRepository = InMemoryMembershipRepository()
    assert repository.get(_actor(), _workspace()) is None


def test_empty_repository_missing_operations_do_not_create() -> None:
    repository = InMemoryMembershipRepository()
    actor, workspace = _actor(), _workspace()

    assert repository.get(actor, workspace) is None
    assert repository.activate(actor, workspace) is None
    assert repository.deactivate(actor, workspace) is None
    assert repository.get(actor, workspace) is None


def test_create_missing_is_active_and_repeated_create_is_idempotent() -> None:
    repository = InMemoryMembershipRepository()
    actor, workspace = _actor(), _workspace()

    created = repository.create(actor, workspace)
    repeated = repository.create(actor, workspace)

    assert created == _membership(actor, workspace)
    assert repeated is created
    assert repository.get(actor, workspace) is created


def test_create_never_reactivates_existing_inactive_membership() -> None:
    inactive = _membership(status=MembershipStatus.INACTIVE)
    repository = InMemoryMembershipRepository((inactive,))

    result = repository.create(inactive.actor, inactive.workspace)

    assert result is inactive
    assert result.status is MembershipStatus.INACTIVE


def test_activate_transitions_only_inactive_and_is_idempotent() -> None:
    inactive = _membership(status=MembershipStatus.INACTIVE)
    repository = InMemoryMembershipRepository((inactive,))

    activated = repository.activate(inactive.actor, inactive.workspace)
    repeated = repository.activate(inactive.actor, inactive.workspace)

    assert activated.status is MembershipStatus.ACTIVE
    assert activated.actor is inactive.actor
    assert activated.workspace is inactive.workspace
    assert repeated is activated


def test_deactivate_transitions_only_active_and_is_idempotent() -> None:
    active = _membership()
    repository = InMemoryMembershipRepository((active,))

    deactivated = repository.deactivate(active.actor, active.workspace)
    repeated = repository.deactivate(active.actor, active.workspace)

    assert deactivated.status is MembershipStatus.INACTIVE
    assert deactivated.actor is active.actor
    assert deactivated.workspace is active.workspace
    assert repeated is deactivated


def test_exact_actor_workspace_pairs_are_isolated_and_case_sensitive() -> None:
    repository = InMemoryMembershipRepository()
    actor_a, actor_b = _actor("actor"), _actor("other")
    workspace_a, workspace_b = _workspace("workspace"), _workspace("other")
    case_actor, case_workspace = _actor("Actor"), _workspace("Workspace")

    records = (
        repository.create(actor_a, workspace_a),
        repository.create(actor_a, workspace_b),
        repository.create(actor_b, workspace_a),
        repository.create(case_actor, case_workspace),
    )

    assert len(set(records)) == 4
    assert repository.get(actor_a, workspace_a) is records[0]
    assert repository.get(actor_a, workspace_b) is records[1]
    assert repository.get(actor_b, workspace_a) is records[2]
    assert repository.get(case_actor, case_workspace) is records[3]


def test_initial_collection_is_defensively_captured() -> None:
    initial = [_membership()]
    repository = InMemoryMembershipRepository(initial)
    initial.clear()

    assert repository.get(_actor(), _workspace()) == _membership()


def test_duplicate_initial_identity_is_rejected() -> None:
    active = _membership()
    inactive = _membership(status=MembershipStatus.INACTIVE)
    with pytest.raises(ValueError, match="unique"):
        InMemoryMembershipRepository((active, inactive))


@pytest.mark.parametrize("invalid", ("memberships", b"memberships", (object(),)))
def test_invalid_initial_collection_is_rejected(invalid) -> None:
    with pytest.raises((TypeError, ValueError)):
        InMemoryMembershipRepository(invalid)


def test_returned_membership_is_immutable() -> None:
    membership = InMemoryMembershipRepository().create(_actor(), _workspace())
    with pytest.raises(FrozenInstanceError):
        membership.status = MembershipStatus.INACTIVE
