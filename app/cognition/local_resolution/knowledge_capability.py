"""Typed knowledge capability with authorization before repository access."""

from app.cognition.local_resolution.capability import LocalPermissionDenied
from app.cognition.local_resolution.contracts import (
    KnowledgeRecordRepository,
    PermissionPolicy,
)
from app.cognition.local_resolution.models import (
    KNOWLEDGE_DISCOVERY_MAX_RESULTS,
    ActorIdentity,
    FindKnowledgeRecordsQuery,
    KnowledgeRead,
    KnowledgeRecordsFound,
    KnowledgeStored,
    ReadKnowledgeRecordQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    KNOWLEDGE_RECORDS_ADD,
    KNOWLEDGE_RECORDS_READ,
)


class StructuredKnowledgeCapability:
    def __init__(
        self, repository: KnowledgeRecordRepository, permissions: PermissionPolicy
    ) -> None:
        self._repository = repository
        self._permissions = permissions

    def execute(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        intent: StoreKnowledgeRecordCommand
        | ReadKnowledgeRecordQuery
        | FindKnowledgeRecordsQuery,
    ) -> KnowledgeStored | KnowledgeRead | KnowledgeRecordsFound:
        if isinstance(intent, StoreKnowledgeRecordCommand):
            action = KNOWLEDGE_RECORDS_ADD
        elif isinstance(intent, (ReadKnowledgeRecordQuery, FindKnowledgeRecordsQuery)):
            action = KNOWLEDGE_RECORDS_READ
        else:
            raise TypeError("Unsupported local knowledge intent.")
        if not self._permissions.is_allowed(actor, workspace, action):
            raise LocalPermissionDenied("Local operation is not authorized.")
        if isinstance(intent, StoreKnowledgeRecordCommand):
            if intent.record.workspace != workspace:
                raise ValueError("Intent and record workspaces must match.")
            return self._repository.store(intent.record)
        if isinstance(intent, FindKnowledgeRecordsQuery):
            records = self._repository.find_by_key(workspace, intent.key, intent.kind)
            return KnowledgeRecordsFound(
                records[:KNOWLEDGE_DISCOVERY_MAX_RESULTS],
                len(records) == KNOWLEDGE_DISCOVERY_MAX_RESULTS + 1,
            )
        return self._repository.read(workspace, intent.record_id)
