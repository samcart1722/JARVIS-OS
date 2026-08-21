"""Focused Container composition for durable action permissions."""

import ast
from pathlib import Path

import pytest

from app.cognition.local_resolution.models import (
    ActorIdentity,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_READ,
    ExplicitPermissionPolicy,
    PermissionGrant,
    RepositoryPermissionPolicy,
)
from app.core.config import Settings
from app.core.container import Container


class FalseyPermissionGrantRepository:
    def __init__(
        self,
        *,
        granted: bool = True,
    ) -> None:
        self.granted = granted
        self.reads = []
        self.creates = []

    def __bool__(self) -> bool:
        return False

    def is_granted(
        self,
        actor,
        workspace,
        action,
    ):
        self.reads.append(
            (
                actor,
                workspace,
                action,
            )
        )
        return self.granted

    def create(
        self,
        actor,
        workspace,
        action,
    ):
        self.creates.append(
            (
                actor,
                workspace,
                action,
            )
        )


def test_default_container_keeps_explicit_fail_closed_policy() -> None:
    container = Container(
        Settings(_env_file=None)
    )

    assert isinstance(
        container.local_permission_policy,
        ExplicitPermissionPolicy,
    )

    assert (
        container.local_permission_grant_repository
        is None
    )

    assert not container.local_permission_policy.is_allowed(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
        LIST_ITEMS_READ,
    )


def test_configured_grants_keep_existing_explicit_policy() -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    grant = PermissionGrant(
        actor.actor_id,
        workspace.workspace_id,
        frozenset(
            (
                LIST_ITEMS_READ,
            )
        ),
    )

    container = Container(
        Settings(_env_file=None),
        local_permission_grants=(
            grant,
        ),
    )

    assert isinstance(
        container.local_permission_policy,
        ExplicitPermissionPolicy,
    )

    assert (
        container.local_permission_grant_repository
        is None
    )

    assert container.local_permission_policy.is_allowed(
        actor,
        workspace,
        LIST_ITEMS_READ,
    )


def test_container_preserves_falsey_permission_repository_without_calls(
) -> None:
    repository = FalseyPermissionGrantRepository()

    container = Container(
        Settings(_env_file=None),
        local_permission_grant_repository=repository,
    )

    assert (
        container.local_permission_grant_repository
        is repository
    )

    assert isinstance(
        container.local_permission_policy,
        RepositoryPermissionPolicy,
    )

    assert (
        container.local_permission_policy._repository
        is repository
    )

    assert repository.reads == []
    assert repository.creates == []


def test_repository_policy_is_shared_by_local_capabilities() -> None:
    repository = FalseyPermissionGrantRepository(
        granted=True,
    )

    container = Container(
        Settings(_env_file=None),
        local_permission_grant_repository=repository,
    )

    assert (
        container.structured_list_capability._permissions
        is container.local_permission_policy
    )

    assert (
        container.structured_knowledge_capability._permissions
        is container.local_permission_policy
    )

    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    result = container.local_first_resolver.resolve(
        actor,
        workspace,
        ReadListItemsQuery("shopping"),
    )

    assert result.success
    assert result.items == ()

    assert repository.reads == [
        (
            actor,
            workspace,
            LIST_ITEMS_READ,
        )
    ]

    assert repository.creates == []


def test_container_rejects_ambiguous_permission_ownership() -> None:
    repository = FalseyPermissionGrantRepository()

    grant = PermissionGrant(
        "actor",
        "workspace",
        frozenset(
            (
                LIST_ITEMS_READ,
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="Permission policy ownership is ambiguous",
    ):
        Container(
            Settings(_env_file=None),
            local_permission_grants=(
                grant,
            ),
            local_permission_grant_repository=repository,
        )


def test_repository_denial_flows_through_existing_capability() -> None:
    repository = FalseyPermissionGrantRepository(
        granted=False,
    )

    container = Container(
        Settings(_env_file=None),
        local_permission_grant_repository=repository,
    )

    result = container.local_first_resolver.resolve(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
        ReadListItemsQuery("shopping"),
    )

    assert result.handled
    assert not result.success

    assert (
        result.error_code
        == "local_permission_denied"
    )


def test_core_container_does_not_import_sqlite_or_infrastructure() -> None:
    source = Path(
        "app/core/container.py"
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    imported_modules = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imported_modules.append(
                    node.module
                )

        elif isinstance(node, ast.Import):
            imported_modules.extend(
                alias.name
                for alias in node.names
            )

    assert "sqlite3" not in imported_modules

    assert not any(
        module.startswith(
            "app.infrastructure"
        )
        for module in imported_modules
    )
