"""Deterministic actor-workspace membership decision service."""

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.membership.contracts import MembershipRepository, MembershipRepositoryError
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
)


class MembershipDecisionService:
    def __init__(self, repository: MembershipRepository) -> None:
        if repository is None:
            raise ValueError("A membership repository is required.")
        self._repository = repository

    def decide(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> MembershipDecision:
        if type(actor) is not ActorIdentity:
            raise ValueError("Membership actor is invalid.")
        if type(workspace) is not WorkspaceIdentity:
            raise ValueError("Membership workspace is invalid.")
        try:
            membership = self._repository.get(actor, workspace)
        except MembershipRepositoryError:
            return MembershipDecision(False, error_code=MEMBERSHIP_RESOLUTION_FAILED)
        if membership is None:
            return MembershipDecision(False, error_code=MEMBERSHIP_NOT_FOUND)
        if type(membership) is not ActorWorkspaceMembership:
            return MembershipDecision(False, error_code=MEMBERSHIP_RESOLUTION_FAILED)
        if membership.status is MembershipStatus.INACTIVE:
            return MembershipDecision(False, error_code=MEMBERSHIP_INACTIVE)
        return MembershipDecision(True, membership)
