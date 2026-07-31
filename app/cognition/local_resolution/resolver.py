"""Deterministic resolver for already-typed local intents."""

from app.cognition.local_resolution.capability import (
    LocalPermissionDenied,
    StructuredListCapability,
)
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_NOT_HANDLED_ROUTE,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    AddListItemsCommand,
    ListItemsAdded,
    ListItemsSnapshot,
    LocalResolutionResult,
    ReadListItemsQuery,
    WorkspaceIdentity,
)


class LocalFirstResolver:
    def __init__(self, list_capability: StructuredListCapability) -> None:
        self._list_capability = list_capability

    def resolve(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        intent: object,
    ) -> LocalResolutionResult:
        if not isinstance(actor, ActorIdentity) or not isinstance(
            workspace, WorkspaceIdentity
        ):
            return LocalResolutionResult(
                True,
                False,
                "Local operation could not be completed.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_VALIDATION_FAILED,
            )
        if not isinstance(intent, (AddListItemsCommand, ReadListItemsQuery)):
            return LocalResolutionResult(False, False, "", LOCAL_NOT_HANDLED_ROUTE)
        try:
            result = self._list_capability.execute(actor, workspace, intent)
        except LocalPermissionDenied:
            return LocalResolutionResult(
                True,
                False,
                "Local operation denied.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_PERMISSION_DENIED,
            )
        except (TypeError, ValueError):
            return LocalResolutionResult(
                True,
                False,
                "Local operation could not be completed.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_VALIDATION_FAILED,
            )
        if isinstance(result, ListItemsAdded):
            return LocalResolutionResult(
                True,
                True,
                "List updated locally.",
                LOCAL_CAPABILITY_ROUTE,
                added=result.added,
                already_present=result.already_present,
                items=result.items,
            )
        if isinstance(result, ListItemsSnapshot):
            return LocalResolutionResult(
                True,
                True,
                "List read locally.",
                LOCAL_CAPABILITY_ROUTE,
                items=result.items,
            )
        return LocalResolutionResult(
            True,
            False,
            "Local operation could not be completed.",
            LOCAL_CAPABILITY_ROUTE,
            error_code=LOCAL_VALIDATION_FAILED,
        )
