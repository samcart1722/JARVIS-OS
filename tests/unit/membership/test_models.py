from dataclasses import FrozenInstanceError, fields

import pytest

import app.membership as membership_package
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
)
from app.membership.service import MembershipDecisionService


def _membership(
    status: MembershipStatus = MembershipStatus.ACTIVE,
) -> ActorWorkspaceMembership:
    return ActorWorkspaceMembership(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
        status,
    )


def test_membership_status_has_exact_public_states_and_values() -> None:
    assert tuple(MembershipStatus) == (
        MembershipStatus.ACTIVE,
        MembershipStatus.INACTIVE,
    )
    assert MembershipStatus.ACTIVE.value == "active"
    assert MembershipStatus.INACTIVE.value == "inactive"


@pytest.mark.parametrize("status", tuple(MembershipStatus))
def test_membership_preserves_exact_canonical_identities(status) -> None:
    actor = ActorIdentity(" Actor ")
    workspace = WorkspaceIdentity(" Workspace ")
    membership = ActorWorkspaceMembership(actor, workspace, status)

    assert membership.actor is actor
    assert membership.workspace is workspace
    assert membership.actor.actor_id == "Actor"
    assert membership.workspace.workspace_id == "Workspace"
    assert membership.status is status
    assert tuple(field.name for field in fields(membership)) == (
        "actor",
        "workspace",
        "status",
    )


@pytest.mark.parametrize(
    ("actor", "workspace", "status"),
    (
        (object(), WorkspaceIdentity("workspace"), MembershipStatus.ACTIVE),
        (ActorIdentity("actor"), object(), MembershipStatus.ACTIVE),
        (ActorIdentity("actor"), WorkspaceIdentity("workspace"), "active"),
    ),
)
def test_membership_rejects_invalid_field_types(actor, workspace, status) -> None:
    with pytest.raises(ValueError):
        ActorWorkspaceMembership(actor, workspace, status)


def test_membership_is_frozen_and_slotted() -> None:
    membership = _membership()
    with pytest.raises(FrozenInstanceError):
        membership.status = MembershipStatus.INACTIVE
    assert not hasattr(membership, "__dict__")


def test_active_membership_decision_is_valid_and_frozen() -> None:
    membership = _membership()
    decision = MembershipDecision(True, membership)

    assert decision.success is True
    assert decision.membership is membership
    assert decision.error_code is None
    with pytest.raises(FrozenInstanceError):
        decision.success = False
    assert not hasattr(decision, "__dict__")


@pytest.mark.parametrize(
    "error_code",
    (MEMBERSHIP_NOT_FOUND, MEMBERSHIP_INACTIVE, MEMBERSHIP_RESOLUTION_FAILED),
)
def test_each_exact_membership_failure_is_valid(error_code) -> None:
    decision = MembershipDecision(False, error_code=error_code)
    assert decision == MembershipDecision(False, None, error_code)


@pytest.mark.parametrize(
    "args",
    (
        (1,),
        (True,),
        (True, _membership(MembershipStatus.INACTIVE)),
        (True, _membership(), MEMBERSHIP_NOT_FOUND),
        (False, _membership(), MEMBERSHIP_NOT_FOUND),
        (False,),
        (False, None, "unsupported_membership_error"),
    ),
)
def test_membership_decision_rejects_invalid_combinations(args) -> None:
    with pytest.raises(ValueError):
        MembershipDecision(*args)


def test_package_exports_exact_block_a_surface() -> None:
    assert membership_package.__all__ == [
        "MEMBERSHIP_INACTIVE",
        "MEMBERSHIP_NOT_FOUND",
        "MEMBERSHIP_RESOLUTION_FAILED",
        "ActorWorkspaceMembership",
        "InMemoryMembershipRepository",
        "MembershipDecision",
        "MembershipDecisionService",
        "MembershipRepository",
        "MembershipRepositoryError",
        "MembershipStatus",
    ]
    assert membership_package.MembershipDecisionService is MembershipDecisionService
