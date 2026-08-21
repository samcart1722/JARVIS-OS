"""Focused contract proof for repository-backed action permissions."""

from unittest.mock import Mock

import pytest

from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.contracts import (
    PermissionGrantRepositoryError,
)
from app.cognition.local_resolution.models import (
    LOCAL_PERMISSION_DENIED,
    ActorIdentity,
    ReadListItemsQuery,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_READ,
    RepositoryPermissionPolicy,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver


class ExactPermissionRepository:
    def __init__(
        self,
        grants: frozenset[tuple[str, str, str]] = frozenset(),
    ) -> None:
        self._grants = grants

    def is_granted(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> bool:
        return (
            actor.actor_id,
            workspace.workspace_id,
            action,
        ) in self._grants

    def create(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        action: str,
    ) -> None:
        raise NotImplementedError


def test_repository_permission_policy_requires_repository() -> None:
    with pytest.raises(
        ValueError,
        match="permission grant repository",
    ):
        RepositoryPermissionPolicy(None)


def test_repository_permission_policy_allows_exact_grant() -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")
    repository = ExactPermissionRepository(
        frozenset(
            {
                (
                    actor.actor_id,
                    workspace.workspace_id,
                    LIST_ITEMS_READ,
                )
            }
        )
    )
    policy = RepositoryPermissionPolicy(repository)

    assert policy.is_allowed(
        actor,
        workspace,
        LIST_ITEMS_READ,
    )


@pytest.mark.parametrize(
    ("actor_id", "workspace_id", "action"),
    (
        ("Actor", "workspace", LIST_ITEMS_READ),
        ("actor", "Workspace", LIST_ITEMS_READ),
        ("actor", "workspace", "LIST.ITEMS.READ"),
        ("actor", "workspace", " list.items.read "),
        ("other", "workspace", LIST_ITEMS_READ),
        ("actor", "other", LIST_ITEMS_READ),
    ),
)
def test_repository_permission_policy_matching_is_exact(
    actor_id: str,
    workspace_id: str,
    action: str,
) -> None:
    repository = ExactPermissionRepository(
        frozenset(
            {
                (
                    "actor",
                    "workspace",
                    LIST_ITEMS_READ,
                )
            }
        )
    )
    policy = RepositoryPermissionPolicy(repository)

    assert not policy.is_allowed(
        ActorIdentity(actor_id),
        WorkspaceIdentity(workspace_id),
        action,
    )


def test_repository_permission_policy_denies_missing_grant() -> None:
    repository = Mock()
    repository.is_granted.return_value = False
    policy = RepositoryPermissionPolicy(repository)

    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")

    assert not policy.is_allowed(
        actor,
        workspace,
        LIST_ITEMS_READ,
    )

    repository.is_granted.assert_called_once_with(
        actor,
        workspace,
        LIST_ITEMS_READ,
    )


def test_repository_permission_policy_fails_closed_on_repository_error() -> None:
    repository = Mock()
    repository.is_granted.side_effect = (
        PermissionGrantRepositoryError(
            "private storage detail"
        )
    )
    policy = RepositoryPermissionPolicy(repository)

    assert not policy.is_allowed(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
        LIST_ITEMS_READ,
    )


def test_repository_permission_policy_fails_closed_on_invalid_result() -> None:
    repository = Mock()
    repository.is_granted.return_value = 1
    policy = RepositoryPermissionPolicy(repository)

    assert not policy.is_allowed(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
        LIST_ITEMS_READ,
    )


def test_repository_permission_policy_does_not_swallow_programming_errors() -> None:
    repository = Mock()
    repository.is_granted.side_effect = RuntimeError(
        "programming defect"
    )
    policy = RepositoryPermissionPolicy(repository)

    with pytest.raises(
        RuntimeError,
        match="programming defect",
    ):
        policy.is_allowed(
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
        )


@pytest.mark.parametrize(
    ("actor", "workspace", "action", "error"),
    (
        (
            None,
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
            TypeError,
        ),
        (
            object(),
            WorkspaceIdentity("workspace"),
            LIST_ITEMS_READ,
            TypeError,
        ),
        (
            ActorIdentity("actor"),
            None,
            LIST_ITEMS_READ,
            TypeError,
        ),
        (
            ActorIdentity("actor"),
            object(),
            LIST_ITEMS_READ,
            TypeError,
        ),
        (
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            None,
            ValueError,
        ),
        (
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            "",
            ValueError,
        ),
        (
            ActorIdentity("actor"),
            WorkspaceIdentity("workspace"),
            " ",
            ValueError,
        ),
    ),
)
def test_repository_permission_policy_rejects_invalid_boundary_input(
    actor,
    workspace,
    action,
    error,
) -> None:
    repository = Mock()
    policy = RepositoryPermissionPolicy(repository)

    with pytest.raises(error):
        policy.is_allowed(
            actor,
            workspace,
            action,
        )

    repository.is_granted.assert_not_called()


def test_repository_failure_denies_before_data_repository_access() -> None:
    permission_repository = Mock()
    permission_repository.is_granted.side_effect = (
        PermissionGrantRepositoryError(
            "private storage detail"
        )
    )

    data_repository = Mock()

    resolver = LocalFirstResolver(
        StructuredListCapability(
            data_repository,
            RepositoryPermissionPolicy(
                permission_repository
            ),
        )
    )

    result = resolver.resolve(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
        ReadListItemsQuery("list"),
    )

    assert result.handled
    assert not result.success
    assert result.error_code == LOCAL_PERMISSION_DENIED
    assert not result.model_used
    assert not result.external_access

    data_repository.read.assert_not_called()
    data_repository.add.assert_not_called()
