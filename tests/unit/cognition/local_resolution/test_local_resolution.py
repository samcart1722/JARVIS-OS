"""Focused proof of generic deterministic local resolution."""

from dataclasses import FrozenInstanceError
from unittest.mock import Mock

import pytest

from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_NOT_HANDLED_ROUTE,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    AddListItemsCommand,
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


@pytest.mark.parametrize(
    ("factory", "value"),
    ((ActorIdentity, " "), (WorkspaceIdentity, ""), (ReadListItemsQuery, "\t")),
)
def test_identifiers_reject_blank(factory, value) -> None:
    with pytest.raises(ValueError):
        factory(value)


def test_add_command_normalizes_and_is_frozen() -> None:
    command = AddListItemsCommand(" list ", (" diapers ", "grapes"))
    assert command.list_id == "list" and command.items == ("diapers", "grapes")
    with pytest.raises(FrozenInstanceError):
        command.list_id = "other"


@pytest.mark.parametrize("items", ((), (" ",), ("ok", "")))
def test_add_command_rejects_empty_items(items) -> None:
    with pytest.raises(ValueError):
        AddListItemsCommand("list", items)


def _resolver(*actions: str):
    repository = InMemoryListItemRepository()
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")
    policy = ExplicitPermissionPolicy(
        (PermissionGrant("actor", "workspace", frozenset(actions)),)
    )
    return (
        LocalFirstResolver(StructuredListCapability(repository, policy)),
        actor,
        workspace,
    )


def test_repository_empty_add_order_snapshot_duplicates_and_isolation() -> None:
    repository = InMemoryListItemRepository()
    one = WorkspaceIdentity("one")
    two = WorkspaceIdentity("two")
    assert repository.read(one, "a").items == ()
    result = repository.add(one, "a", ("Diapers", "grapes", " diapers "))
    assert result.added == ("Diapers", "grapes")
    assert result.already_present == ("diapers",)
    assert result.items == ("Diapers", "grapes")
    snapshot = repository.read(one, "a")
    repository.add(one, "a", ("milk",))
    assert snapshot.items == ("Diapers", "grapes")
    assert repository.read(one, "b").items == ()
    assert repository.read(two, "a").items == ()


def test_permission_policy_allows_explicit_actions_and_denies_unknown() -> None:
    resolver, actor, workspace = _resolver(LIST_ITEMS_ADD, LIST_ITEMS_READ)
    added = resolver.resolve(actor, workspace, AddListItemsCommand("list", ("x",)))
    read = resolver.resolve(actor, workspace, ReadListItemsQuery("list"))
    assert added.success and read.items == ("x",)
    policy = ExplicitPermissionPolicy()
    assert not policy.is_allowed(actor, workspace, "unknown")


def test_permission_grant_normalizes_identity_and_actions() -> None:
    grant = PermissionGrant(" actor ", " workspace ", frozenset((" list.items.read ",)))
    assert grant.actor_id == "actor"
    assert grant.workspace_id == "workspace"
    assert grant.actions == frozenset((LIST_ITEMS_READ,))


@pytest.mark.parametrize(
    ("actor_id", "workspace_id"),
    (
        (None, "workspace"),
        (object(), "workspace"),
        (" ", "workspace"),
        ("actor", None),
        ("actor", object()),
        ("actor", " "),
    ),
)
def test_permission_grant_rejects_invalid_identities(actor_id, workspace_id) -> None:
    with pytest.raises(ValueError):
        PermissionGrant(actor_id, workspace_id, frozenset((LIST_ITEMS_READ,)))


@pytest.mark.parametrize(
    "actions",
    (
        set((LIST_ITEMS_READ,)),
        (LIST_ITEMS_READ,),
        None,
        frozenset(),
        frozenset((" ",)),
        frozenset((1,)),
    ),
)
def test_permission_grant_rejects_invalid_actions(actions) -> None:
    with pytest.raises(ValueError):
        PermissionGrant("actor", "workspace", actions)


@pytest.mark.parametrize(
    "intent", (AddListItemsCommand("l", ("x",)), ReadListItemsQuery("l"))
)
def test_denial_precedes_repository_access_and_discloses_nothing(intent) -> None:
    repository = Mock()
    capability = StructuredListCapability(repository, ExplicitPermissionPolicy())
    result = LocalFirstResolver(capability).resolve(
        ActorIdentity("actor"), WorkspaceIdentity("workspace"), intent
    )
    assert result.handled and not result.success
    assert result.error_code == LOCAL_PERMISSION_DENIED and result.items == ()
    repository.add.assert_not_called()
    repository.read.assert_not_called()


def test_supported_and_unsupported_route_metadata() -> None:
    resolver, actor, workspace = _resolver(LIST_ITEMS_READ)
    local = resolver.resolve(actor, workspace, ReadListItemsQuery("list"))
    unsupported = resolver.resolve(actor, workspace, object())
    assert local.resolution_route == LOCAL_CAPABILITY_ROUTE
    assert not local.model_used and not local.external_access
    assert not unsupported.handled
    assert unsupported.resolution_route == LOCAL_NOT_HANDLED_ROUTE


def test_repository_validation_failure_is_safe_and_terminal() -> None:
    repository = Mock()
    repository.read.side_effect = ValueError("private state")
    permission = Mock()
    permission.is_allowed.return_value = True
    resolver = LocalFirstResolver(StructuredListCapability(repository, permission))
    result = resolver.resolve(
        ActorIdentity("actor"), WorkspaceIdentity("workspace"), ReadListItemsQuery("l")
    )
    assert result.error_code == LOCAL_VALIDATION_FAILED
    assert "private state" not in result.response
    assert not result.model_used and not result.external_access


@pytest.mark.parametrize(
    ("actor", "workspace"),
    (
        (None, WorkspaceIdentity("workspace")),
        (object(), WorkspaceIdentity("workspace")),
        (ActorIdentity("actor"), None),
        (ActorIdentity("actor"), object()),
    ),
)
def test_invalid_runtime_identity_is_safe_and_never_accesses_repository(
    actor, workspace
) -> None:
    repository = Mock()
    resolver = LocalFirstResolver(
        StructuredListCapability(repository, ExplicitPermissionPolicy())
    )
    result = resolver.resolve(actor, workspace, ReadListItemsQuery("list"))
    assert result.handled and not result.success
    assert result.error_code == LOCAL_VALIDATION_FAILED
    assert result.resolution_route == LOCAL_CAPABILITY_ROUTE
    assert not result.model_used and not result.external_access
    assert "AttributeError" not in result.response
    repository.add.assert_not_called()
    repository.read.assert_not_called()
