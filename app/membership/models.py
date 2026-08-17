"""Immutable actor-workspace membership values and decisions."""

from dataclasses import dataclass
from enum import Enum

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity

MEMBERSHIP_NOT_FOUND = "membership_not_found"
MEMBERSHIP_INACTIVE = "membership_inactive"
MEMBERSHIP_RESOLUTION_FAILED = "membership_resolution_failed"

_MEMBERSHIP_ERROR_CODES = frozenset(
    (
        MEMBERSHIP_NOT_FOUND,
        MEMBERSHIP_INACTIVE,
        MEMBERSHIP_RESOLUTION_FAILED,
    )
)


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass(frozen=True, slots=True)
class ActorWorkspaceMembership:
    actor: ActorIdentity
    workspace: WorkspaceIdentity
    status: MembershipStatus

    def __post_init__(self) -> None:
        if type(self.actor) is not ActorIdentity:
            raise ValueError("Membership actor is invalid.")
        if type(self.workspace) is not WorkspaceIdentity:
            raise ValueError("Membership workspace is invalid.")
        if type(self.status) is not MembershipStatus:
            raise ValueError("Membership status is invalid.")


@dataclass(frozen=True, slots=True)
class MembershipDecision:
    success: bool
    membership: ActorWorkspaceMembership | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise ValueError("Membership decision success must be explicit.")
        if self.success:
            if type(self.membership) is not ActorWorkspaceMembership:
                raise ValueError("Successful membership decision requires membership.")
            if self.membership.status is not MembershipStatus.ACTIVE:
                raise ValueError(
                    "Successful membership decision requires active status."
                )
            if self.error_code is not None:
                raise ValueError("Successful membership decision forbids an error.")
            return
        if self.membership is not None:
            raise ValueError("Failed membership decision forbids membership.")
        if self.error_code not in _MEMBERSHIP_ERROR_CODES:
            raise ValueError("Failed membership decision requires a valid error.")
