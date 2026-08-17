"""Deterministic process-local actor-workspace membership repository."""

from collections.abc import Iterable

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.membership.models import ActorWorkspaceMembership, MembershipStatus


class InMemoryMembershipRepository:
    def __init__(
        self,
        memberships: Iterable[ActorWorkspaceMembership] = (),
    ) -> None:
        if isinstance(memberships, (str, bytes)):
            raise TypeError("Memberships must be a collection of memberships.")
        captured = tuple(memberships)
        records: dict[tuple[str, str], ActorWorkspaceMembership] = {}
        for membership in captured:
            if type(membership) is not ActorWorkspaceMembership:
                raise ValueError("Initial membership is invalid.")
            key = self._key(membership.actor, membership.workspace)
            if key in records:
                raise ValueError("Initial membership identities must be unique.")
            records[key] = membership
        self._memberships = records

    @staticmethod
    def _key(
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> tuple[str, str]:
        if type(actor) is not ActorIdentity:
            raise ValueError("Membership actor is invalid.")
        if type(workspace) is not WorkspaceIdentity:
            raise ValueError("Membership workspace is invalid.")
        return actor.actor_id, workspace.workspace_id

    def get(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership | None:
        return self._memberships.get(self._key(actor, workspace))

    def create(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership:
        key = self._key(actor, workspace)
        existing = self._memberships.get(key)
        if existing is not None:
            return existing
        membership = ActorWorkspaceMembership(
            actor,
            workspace,
            MembershipStatus.ACTIVE,
        )
        self._memberships[key] = membership
        return membership

    def activate(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership | None:
        key = self._key(actor, workspace)
        existing = self._memberships.get(key)
        if existing is None or existing.status is MembershipStatus.ACTIVE:
            return existing
        membership = ActorWorkspaceMembership(
            existing.actor,
            existing.workspace,
            MembershipStatus.ACTIVE,
        )
        self._memberships[key] = membership
        return membership

    def deactivate(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
    ) -> ActorWorkspaceMembership | None:
        key = self._key(actor, workspace)
        existing = self._memberships.get(key)
        if existing is None or existing.status is MembershipStatus.INACTIVE:
            return existing
        membership = ActorWorkspaceMembership(
            existing.actor,
            existing.workspace,
            MembershipStatus.INACTIVE,
        )
        self._memberships[key] = membership
        return membership
