"""Authorized, bounded knowledge metadata exploration without routing authority."""

from app.cognition.local_resolution.capability import LocalPermissionDenied
from app.cognition.local_resolution.contracts import (
    KnowledgeBrowseRepository,
    LocalRepositoryError,
    PermissionPolicy,
)
from app.cognition.local_resolution.models import (
    KNOWLEDGE_DISCOVERY_LOOKAHEAD,
    KNOWLEDGE_DISCOVERY_MAX_RESULTS,
    ActorIdentity,
    BrowseKnowledgeRecordsQuery,
    KnowledgeRecordsBrowsed,
    WorkspaceIdentity,
    _validate_browse_summaries,
)
from app.cognition.local_resolution.permissions import KNOWLEDGE_RECORDS_BROWSE


class StructuredKnowledgeBrowseCapability:
    """Return metadata or raise at the existing local capability boundaries.

    Denial raises LocalPermissionDenied; invalid inputs/returns raise TypeError
    or ValueError. Declared storage failures are sanitized as LocalRepositoryError.
    The later resolver owns conversion to local_permission_denied or
    local_validation_failed, with no partial results. Unexpected exceptions are
    not converted here. Permission repository failures retain their policy's
    existing handling. This component owns neither routing nor HTTP errors.
    """

    def __init__(
        self, repository: KnowledgeBrowseRepository, permissions: PermissionPolicy
    ) -> None:
        self._repository = repository
        self._permissions = permissions

    def execute(
        self,
        actor: ActorIdentity,
        workspace: WorkspaceIdentity,
        intent: BrowseKnowledgeRecordsQuery,
    ) -> KnowledgeRecordsBrowsed:
        if type(intent) is not BrowseKnowledgeRecordsQuery:
            raise TypeError("Unsupported local knowledge browse intent.")
        if type(actor) is not ActorIdentity or type(workspace) is not WorkspaceIdentity:
            raise ValueError("Explicit actor and workspace identities are required.")
        allowed = self._permissions.is_allowed(
            actor, workspace, KNOWLEDGE_RECORDS_BROWSE
        )
        if allowed is not True:
            raise LocalPermissionDenied("Local knowledge browse is not authorized.")
        try:
            records = self._repository.browse(workspace)
        except LocalRepositoryError:
            raise LocalRepositoryError(
                "Local knowledge browse could not be completed."
            ) from None
        _validate_browse_summaries(records, KNOWLEDGE_DISCOVERY_LOOKAHEAD, workspace)
        return KnowledgeRecordsBrowsed(
            records[:KNOWLEDGE_DISCOVERY_MAX_RESULTS],
            len(records) == KNOWLEDGE_DISCOVERY_LOOKAHEAD,
        )
