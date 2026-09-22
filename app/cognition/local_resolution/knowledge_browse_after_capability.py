"""Authorized metadata continuation, independent of routing and storage."""

from app.cognition.local_resolution.capability import LocalPermissionDenied
from app.cognition.local_resolution.contracts import (
    KnowledgeBrowseAfterRepository,
    LocalRepositoryError,
    PermissionPolicy,
)
from app.cognition.local_resolution.models import (
    KNOWLEDGE_DISCOVERY_LOOKAHEAD,
    KNOWLEDGE_DISCOVERY_MAX_RESULTS,
    ActorIdentity,
    BrowseAfterKnowledgeRecordsQuery,
    KnowledgeRecordsBrowsed,
    WorkspaceIdentity,
    _validate_browse_summaries,
)
from app.cognition.local_resolution.permissions import KNOWLEDGE_RECORDS_BROWSE


class StructuredKnowledgeBrowseAfterCapability:
    """Use the existing denial, validation and repository-error boundaries.

    Permission dependency failures retain the policy's existing handling.
    Resolver integration owns terminal error mapping in a later block.
    """

    def __init__(
        self, repository: KnowledgeBrowseAfterRepository, permissions: PermissionPolicy
    ) -> None:
        self._repository = repository
        self._permissions = permissions

    def execute(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        intent: BrowseAfterKnowledgeRecordsQuery,
    ) -> KnowledgeRecordsBrowsed:
        if type(intent) is not BrowseAfterKnowledgeRecordsQuery:
            raise TypeError("Unsupported local knowledge browse-after intent.")
        if type(actor) is not ActorIdentity or type(workspace) is not WorkspaceIdentity:
            raise ValueError("Explicit actor and workspace identities are required.")
        allowed = self._permissions.is_allowed(
            actor, workspace, KNOWLEDGE_RECORDS_BROWSE
        )
        if allowed is not True:
            raise LocalPermissionDenied(
                "Local knowledge browse-after is not authorized."
            )
        try:
            records = self._repository.browse_after(workspace, intent.after_record_id)
        except LocalRepositoryError:
            raise LocalRepositoryError(
                "Local knowledge browse-after could not be completed."
            ) from None
        _validate_browse_summaries(records, KNOWLEDGE_DISCOVERY_LOOKAHEAD, workspace)
        if any(record.record_id <= intent.after_record_id for record in records):
            raise ValueError("Knowledge browse-after lower bound is invalid.")
        return KnowledgeRecordsBrowsed(
            records[:KNOWLEDGE_DISCOVERY_MAX_RESULTS],
            len(records) == KNOWLEDGE_DISCOVERY_LOOKAHEAD,
        )
