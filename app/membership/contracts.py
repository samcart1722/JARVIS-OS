"""Infrastructure-independent actor-workspace membership contracts."""

from typing import Protocol

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.membership.models import ActorWorkspaceMembership


class MembershipRepositoryError(RuntimeError):
    """Signal a safe membership repository failure."""


class MembershipRepository(Protocol):
    def get(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership | None: ...

    def create(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership: ...

    def activate(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership | None: ...

    def deactivate(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership | None: ...
