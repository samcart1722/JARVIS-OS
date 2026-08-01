"""Small deny-by-default permission policy for local capabilities."""

from dataclasses import dataclass

from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity

LIST_ITEMS_ADD = "list.items.add"
LIST_ITEMS_READ = "list.items.read"
KNOWLEDGE_RECORDS_ADD = "knowledge.records.add"
KNOWLEDGE_RECORDS_READ = "knowledge.records.read"


@dataclass(frozen=True, slots=True)
class PermissionGrant:
    actor_id: str
    workspace_id: str
    actions: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("Permission grant identities cannot be empty.")
        if not isinstance(self.workspace_id, str) or not self.workspace_id.strip():
            raise ValueError("Permission grant identities cannot be empty.")
        if (
            not isinstance(self.actions, frozenset)
            or not self.actions
            or any(
                not isinstance(action, str) or not action.strip()
                for action in self.actions
            )
        ):
            raise ValueError("Permission grant actions must be non-empty strings.")
        object.__setattr__(self, "actor_id", self.actor_id.strip())
        object.__setattr__(self, "workspace_id", self.workspace_id.strip())
        object.__setattr__(
            self, "actions", frozenset(action.strip() for action in self.actions)
        )


class ExplicitPermissionPolicy:
    def __init__(self, grants: tuple[PermissionGrant, ...] = ()) -> None:
        self._grants = grants

    def is_allowed(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool:
        return any(
            grant.actor_id == actor.actor_id
            and grant.workspace_id == workspace.workspace_id
            and action in grant.actions
            for grant in self._grants
        )
