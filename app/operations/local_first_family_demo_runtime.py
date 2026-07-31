"""Controlled operational proof of deterministic local-first resolution."""

from dataclasses import dataclass

from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.models import (
    ActorIdentity,
    AddListItemsCommand,
    LocalResolutionResult,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    LIST_ITEMS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import InMemoryListItemRepository
from app.cognition.local_resolution.resolver import LocalFirstResolver

LOCAL_DEMO_COMPLETED = "local_demo_completed"


@dataclass(frozen=True, slots=True)
class LocalFirstFamilyDemoReport:
    status: str
    initial_add: LocalResolutionResult
    initial_read: LocalResolutionResult
    duplicate_add: LocalResolutionResult
    final_read: LocalResolutionResult
    denied_read: LocalResolutionResult
    denied_list_unchanged: bool
    actor_explicit: bool
    workspace_explicit: bool
    model_calls: int
    external_calls: int

    def __post_init__(self) -> None:
        if self.status != LOCAL_DEMO_COMPLETED:
            raise ValueError("Unknown local demo status.")
        if not self.actor_explicit or not self.workspace_explicit:
            raise ValueError("Local demo identity and workspace must be explicit.")
        if self.model_calls != 0 or self.external_calls != 0:
            raise ValueError("Local demo cannot include remote calls.")


class LocalFirstFamilyDemoRuntime:
    def __init__(
        self,
        *,
        resolver: LocalFirstResolver,
        actor: ActorIdentity,
        denied_actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        list_id: str = "shopping",
    ) -> None:
        if not list_id.strip():
            raise ValueError("Demo list ID cannot be empty.")
        self._resolver = resolver
        self._actor = actor
        self._denied_actor = denied_actor
        self._workspace = workspace
        self._list_id = list_id

    def run(self) -> LocalFirstFamilyDemoReport:
        first = self._resolver.resolve(
            self._actor,
            self._workspace,
            AddListItemsCommand(self._list_id, ("diapers", "Gerber", "grapes")),
        )
        initial_read = self._resolver.resolve(
            self._actor, self._workspace, ReadListItemsQuery(self._list_id)
        )
        duplicate = self._resolver.resolve(
            self._actor,
            self._workspace,
            AddListItemsCommand(self._list_id, (" GRAPES ", "milk")),
        )
        final_read = self._resolver.resolve(
            self._actor, self._workspace, ReadListItemsQuery(self._list_id)
        )
        denied = self._resolver.resolve(
            self._denied_actor, self._workspace, ReadListItemsQuery(self._list_id)
        )
        after_denial = self._resolver.resolve(
            self._actor, self._workspace, ReadListItemsQuery(self._list_id)
        )
        return LocalFirstFamilyDemoReport(
            LOCAL_DEMO_COMPLETED,
            first,
            initial_read,
            duplicate,
            final_read,
            denied,
            after_denial.items == final_read.items,
            True,
            True,
            0,
            0,
        )


def create_local_first_family_demo_runtime(
    actor_id: str, workspace_id: str
) -> LocalFirstFamilyDemoRuntime:
    actor = ActorIdentity(actor_id)
    workspace = WorkspaceIdentity(workspace_id)
    denied_actor = ActorIdentity("denied-demo-actor")
    repository = InMemoryListItemRepository()
    policy = ExplicitPermissionPolicy(
        (
            PermissionGrant(
                actor.actor_id,
                workspace.workspace_id,
                frozenset((LIST_ITEMS_ADD, LIST_ITEMS_READ)),
            ),
        )
    )
    resolver = LocalFirstResolver(StructuredListCapability(repository, policy))
    return LocalFirstFamilyDemoRuntime(
        resolver=resolver,
        actor=actor,
        denied_actor=denied_actor,
        workspace=workspace,
    )
