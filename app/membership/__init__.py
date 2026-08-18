"""Actor-workspace membership foundation."""

from app.membership.contracts import MembershipRepository, MembershipRepositoryError
from app.membership.in_memory_repository import InMemoryMembershipRepository
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
)
from app.membership.service import MembershipDecisionService

__all__ = [
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
