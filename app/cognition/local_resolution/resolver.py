"""Deterministic resolver for already-typed local intents."""

from app.cognition.local_resolution.capability import (
    LocalPermissionDenied,
    StructuredListCapability,
)
from app.cognition.local_resolution.contracts import (
    KnowledgeRecordConflict,
    LocalRepositoryError,
)
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_NOT_HANDLED_ROUTE,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    AddListItemsCommand,
    FindKnowledgeRecordsQuery,
    KnowledgeDiscoveryResolutionResult,
    KnowledgeRead,
    KnowledgeRecordsFound,
    KnowledgeResolutionResult,
    KnowledgeStored,
    ListItemsAdded,
    ListItemsSnapshot,
    LocalResolutionResult,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)


class LocalFirstResolver:
    def __init__(
        self,
        list_capability: StructuredListCapability,
        knowledge_capability: StructuredKnowledgeCapability | None = None,
    ) -> None:
        self._list_capability = list_capability
        self._knowledge_capability = knowledge_capability

    def resolve(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        intent: object,
    ) -> (
        LocalResolutionResult
        | KnowledgeResolutionResult
        | KnowledgeDiscoveryResolutionResult
    ):
        list_intent = isinstance(intent, (AddListItemsCommand, ReadListItemsQuery))
        knowledge_intent = isinstance(
            intent,
            (
                StoreKnowledgeRecordCommand,
                ReadKnowledgeRecordQuery,
                FindKnowledgeRecordsQuery,
            ),
        )
        if not list_intent and not knowledge_intent:
            return LocalResolutionResult(False, False, "", LOCAL_NOT_HANDLED_ROUTE)
        if knowledge_intent and self._knowledge_capability is None:
            return LocalResolutionResult(False, False, "", LOCAL_NOT_HANDLED_ROUTE)
        if not isinstance(actor, ActorIdentity) or not isinstance(
            workspace, WorkspaceIdentity
        ):
            if isinstance(intent, FindKnowledgeRecordsQuery):
                return KnowledgeDiscoveryResolutionResult(
                    True,
                    False,
                    "Local knowledge discovery could not be completed.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_VALIDATION_FAILED,
                )
            if knowledge_intent:
                return KnowledgeResolutionResult(
                    True,
                    False,
                    "Local knowledge operation could not be completed.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_VALIDATION_FAILED,
                )
            return LocalResolutionResult(
                True,
                False,
                "Local operation could not be completed.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_VALIDATION_FAILED,
            )
        try:
            if list_intent:
                result = self._list_capability.execute(actor, workspace, intent)
            else:
                result = self._knowledge_capability.execute(actor, workspace, intent)
        except LocalPermissionDenied:
            if isinstance(intent, FindKnowledgeRecordsQuery):
                return KnowledgeDiscoveryResolutionResult(
                    True,
                    False,
                    "Local knowledge discovery denied.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_PERMISSION_DENIED,
                )
            if knowledge_intent:
                return KnowledgeResolutionResult(
                    True,
                    False,
                    "Local knowledge operation denied.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_PERMISSION_DENIED,
                )
            return LocalResolutionResult(
                True,
                False,
                "Local operation denied.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_PERMISSION_DENIED,
            )
        except KnowledgeRecordConflict:
            return KnowledgeResolutionResult(
                True,
                False,
                "Knowledge record conflicts with existing local state.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_KNOWLEDGE_CONFLICT,
            )
        except LocalRepositoryError:
            if isinstance(intent, FindKnowledgeRecordsQuery):
                return KnowledgeDiscoveryResolutionResult(
                    True,
                    False,
                    "Local knowledge discovery could not be completed.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_VALIDATION_FAILED,
                )
            if knowledge_intent:
                return KnowledgeResolutionResult(
                    True,
                    False,
                    "Local knowledge operation could not be completed.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_VALIDATION_FAILED,
                )
            return LocalResolutionResult(
                True,
                False,
                "Local operation could not be completed.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_VALIDATION_FAILED,
            )
        except (TypeError, ValueError):
            if isinstance(intent, FindKnowledgeRecordsQuery):
                return KnowledgeDiscoveryResolutionResult(
                    True,
                    False,
                    "Local knowledge discovery could not be completed.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_VALIDATION_FAILED,
                )
            if knowledge_intent:
                return KnowledgeResolutionResult(
                    True,
                    False,
                    "Local knowledge operation could not be completed.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_VALIDATION_FAILED,
                )
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
        if isinstance(result, KnowledgeStored):
            return KnowledgeResolutionResult(
                True,
                True,
                "Knowledge record stored locally.",
                LOCAL_CAPABILITY_ROUTE,
                record=result.record,
                created=result.created,
            )
        if isinstance(result, KnowledgeRead):
            if result.record is None:
                return KnowledgeResolutionResult(
                    True,
                    False,
                    "Knowledge record was not found.",
                    LOCAL_CAPABILITY_ROUTE,
                    error_code=LOCAL_KNOWLEDGE_NOT_FOUND,
                )
            return KnowledgeResolutionResult(
                True,
                True,
                "Knowledge record read locally.",
                LOCAL_CAPABILITY_ROUTE,
                record=result.record,
            )
        if isinstance(result, KnowledgeRecordsFound):
            return KnowledgeDiscoveryResolutionResult(
                True,
                True,
                "Knowledge records found locally.",
                LOCAL_CAPABILITY_ROUTE,
                records=result.records,
                truncated=result.truncated,
            )
        if knowledge_intent:
            return KnowledgeResolutionResult(
                True,
                False,
                "Local knowledge operation could not be completed.",
                LOCAL_CAPABILITY_ROUTE,
                error_code=LOCAL_VALIDATION_FAILED,
            )
        return LocalResolutionResult(
            True,
            False,
            "Local operation could not be completed.",
            LOCAL_CAPABILITY_ROUTE,
            error_code=LOCAL_VALIDATION_FAILED,
        )
