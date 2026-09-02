"""Application gateway over the governed authenticated local-command route."""

from collections import Counter

from app.cognition.domain.cognitive_outcome import COGNITIVE_ERROR_CODES
from app.cognition.interpretation.models import LocalCommandInterpretationStatus
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    AddListItemsCommand,
    FindKnowledgeRecordsQuery,
    KnowledgeDiscoveryResolutionResult,
    KnowledgeKind,
    KnowledgeRecord,
    KnowledgeResolutionResult,
    LocalResolutionResult,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)
from app.local_command.models import (
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationRequest,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    LocalKnowledgeFindProjection,
    LocalKnowledgeReadProjection,
    LocalKnowledgeRecordKind,
    LocalKnowledgeRecordProjection,
    LocalKnowledgeStoreProjection,
    LocalListAddProjection,
    LocalListReadProjection,
    application_error,
)
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
)
from app.principal_authentication.models import (
    LocalAuthenticationProof,
    PrincipalActorMappingErrorCode,
    PrincipalAuthenticationErrorCode,
)
from app.principal_authentication.routing import (
    AuthenticatedLocalCommandRequest,
    AuthenticatedLocalCommandRoutingResult,
    AuthenticatedLocalCommandRoutingService,
    AuthenticatedWorkspaceSelectionErrorCode,
)

_LOCAL_ERROR_MAP = {
    LOCAL_PERMISSION_DENIED: (
        LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED
    ),
    LOCAL_VALIDATION_FAILED: (
        LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED
    ),
    LOCAL_KNOWLEDGE_NOT_FOUND: (
        LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND
    ),
    LOCAL_KNOWLEDGE_CONFLICT: (
        LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT
    ),
}


class LocalCommandApplicationGateway:
    """Translate one safe application request through the governed route."""

    __slots__ = ("_routing_service",)

    def __init__(
        self,
        routing_service: AuthenticatedLocalCommandRoutingService,
    ) -> None:
        if routing_service is None:
            raise ValueError(
                "An authenticated local-command routing service is required."
            )
        self._routing_service = routing_service

    def execute(
        self,
        request: LocalCommandApplicationRequest,
    ) -> LocalCommandApplicationResult:
        if type(request) is not LocalCommandApplicationRequest:
            raise TypeError(
                "A valid local-command application request is required."
            )

        routed = self._routing_service.route(
            AuthenticatedLocalCommandRequest(
                authentication_proof=LocalAuthenticationProof(
                    request.proof
                ),
                requested_workspace_id=request.requested_workspace_id,
                text=request.text,
                fallback_authorization=CognitiveFallbackAuthorization(
                    request.allow_cognitive_fallback
                ),
            )
        )

        if type(routed) is not AuthenticatedLocalCommandRoutingResult:
            raise TypeError(
                "Authenticated routing returned an invalid result."
            )

        return self._map_routed_result(routed)

    def _map_routed_result(
        self,
        routed: AuthenticatedLocalCommandRoutingResult,
    ) -> LocalCommandApplicationResult:
        authentication = routed.authentication_result

        if not authentication.success:
            if (
                authentication.error_code
                is PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.ACCESS_DENIED
                )
            if (
                authentication.error_code
                is PrincipalAuthenticationErrorCode.AUTHENTICATION_RESOLUTION_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE
                )
            raise TypeError(
                "Authentication result contains an unknown failure."
            )

        mapping = routed.mapping_result
        if mapping is None:
            raise TypeError(
                "Authenticated routing omitted principal mapping."
            )

        if not mapping.success:
            if (
                mapping.error_code
                is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.ACCESS_DENIED
                )
            if (
                mapping.error_code
                is PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE
                )
            raise TypeError(
                "Principal mapping contains an unknown failure."
            )

        selection = routed.workspace_selection_result
        if selection is None:
            raise TypeError(
                "Authenticated routing omitted workspace selection."
            )

        if not selection.success:
            if (
                selection.error_code
                is AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.INVALID_REQUEST
                )
            raise TypeError(
                "Workspace selection contains an unknown failure."
            )

        membership = routed.membership_decision
        if membership is None:
            raise TypeError(
                "Authenticated routing omitted membership decision."
            )

        if not membership.success:
            if membership.error_code in (
                MEMBERSHIP_NOT_FOUND,
                MEMBERSHIP_INACTIVE,
            ):
                return self._failure(
                    LocalCommandApplicationErrorCode.ACCESS_DENIED
                )
            if membership.error_code == MEMBERSHIP_RESOLUTION_FAILED:
                return self._failure(
                    LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE
                )
            raise TypeError(
                "Membership decision contains an unknown failure."
            )

        text_routing = routed.text_routing_result
        if text_routing is None:
            raise TypeError(
                "Authenticated routing omitted text-routing result."
            )

        if (
            text_routing.interpretation.status
            is LocalCommandInterpretationStatus.INVALID
        ):
            return self._failure(
                LocalCommandApplicationErrorCode.INVALID_REQUEST
            )

        coordinated = text_routing.coordinated_result
        if coordinated is None:
            raise TypeError(
                "Text routing omitted coordinated result."
            )

        if coordinated.route is CoordinatedRoute.LOCAL:
            return self._map_local_result(
                text_routing.interpretation.intent,
                coordinated.local_result,
                selection.workspace,
            )

        if coordinated.route is CoordinatedRoute.SAFE_INSUFFICIENCY:
            return self._map_safe_insufficiency(
                coordinated.insufficiency_reason
            )

        if coordinated.route is CoordinatedRoute.COGNITIVE:
            return self._map_cognitive_result(
                coordinated.cognitive_outcome
            )

        raise TypeError("Coordinated result contains an unknown route.")

    def _map_local_result(
        self,
        intent,
        local_result,
        selected_workspace: WorkspaceIdentity,
    ) -> LocalCommandApplicationResult:
        if local_result is None:
            raise TypeError(
                "Local coordinated route omitted the local result."
            )

        if local_result.success:
            projection = self._map_local_success_projection(
                intent,
                local_result,
                selected_workspace,
            )
            return LocalCommandApplicationResult(
                True,
                route=LocalCommandApplicationRoute.LOCAL,
                response=local_result.response,
                projection=projection,
            )

        error_code = _LOCAL_ERROR_MAP.get(local_result.error_code)
        if error_code is None:
            raise TypeError(
                "Local result contains an unknown failure."
            )

        return self._failure(
            error_code,
            LocalCommandApplicationRoute.LOCAL,
        )

    @classmethod
    def _map_local_success_projection(
        cls,
        intent,
        local_result,
        selected_workspace: WorkspaceIdentity,
    ) -> (
        LocalListAddProjection
        | LocalListReadProjection
        | LocalKnowledgeStoreProjection
        | LocalKnowledgeReadProjection
        | LocalKnowledgeFindProjection
    ):
        if type(intent) is AddListItemsCommand:
            cls._require_list_success(local_result)
            projection = LocalListAddProjection(
                list_id=intent.list_id,
                added=local_result.added,
                already_present=local_result.already_present,
                items=local_result.items,
            )
            cls._validate_add_projection(intent, projection)
            return projection

        if type(intent) is ReadListItemsQuery:
            cls._require_list_success(local_result)
            if local_result.added or local_result.already_present:
                raise TypeError(
                    "Read list result contains add classification data."
                )
            return LocalListReadProjection(
                list_id=intent.list_id,
                items=local_result.items,
            )

        if type(intent) is StoreKnowledgeRecordCommand:
            cls._require_selected_workspace(selected_workspace)
            cls._require_knowledge_success(local_result)
            if (
                type(intent.record) is not KnowledgeRecord
                or intent.record.workspace != selected_workspace
                or type(local_result.record) is not KnowledgeRecord
                or local_result.record != intent.record
                or type(local_result.created) is not bool
            ):
                raise TypeError(
                    "Knowledge store intent and local result are inconsistent."
                )
            return LocalKnowledgeStoreProjection(
                record=cls._map_knowledge_record(local_result.record),
                created=local_result.created,
            )

        if type(intent) is ReadKnowledgeRecordQuery:
            cls._require_selected_workspace(selected_workspace)
            cls._require_knowledge_success(local_result)
            if (
                type(local_result.record) is not KnowledgeRecord
                or local_result.record.record_id != intent.record_id
                or local_result.record.workspace != selected_workspace
                or local_result.created is not False
            ):
                raise TypeError(
                    "Knowledge read intent and local result are inconsistent."
                )
            return LocalKnowledgeReadProjection(
                record=cls._map_knowledge_record(local_result.record)
            )

        if type(intent) is FindKnowledgeRecordsQuery:
            cls._require_selected_workspace(selected_workspace)
            cls._require_knowledge_discovery_success(local_result)
            if (
                (intent.kind is not None and type(intent.kind) is not KnowledgeKind)
                or
                type(local_result.records) is not tuple
                or any(
                    type(record) is not KnowledgeRecord
                    or record.workspace != selected_workspace
                    or record.key != intent.key
                    or (intent.kind is not None and record.kind is not intent.kind)
                    for record in local_result.records
                )
                or type(local_result.truncated) is not bool
            ):
                raise TypeError(
                    "Knowledge find intent and local result are inconsistent."
                )
            try:
                return LocalKnowledgeFindProjection(
                    records=tuple(
                        cls._map_knowledge_record(record)
                        for record in local_result.records
                    ),
                    truncated=local_result.truncated,
                )
            except ValueError as error:
                raise TypeError(
                    "Knowledge find intent and local result are inconsistent."
                ) from error

        raise TypeError("Successful local result has an unknown intent.")

    @staticmethod
    def _require_list_success(local_result) -> None:
        if (
            type(local_result) is not LocalResolutionResult
            or local_result.handled is not True
            or local_result.success is not True
            or local_result.resolution_route != LOCAL_CAPABILITY_ROUTE
        ):
            raise TypeError("List intent and local result are inconsistent.")

    @staticmethod
    def _require_selected_workspace(selected_workspace) -> None:
        if type(selected_workspace) is not WorkspaceIdentity:
            raise TypeError("Knowledge projection requires a selected workspace.")

    @staticmethod
    def _require_knowledge_success(local_result) -> None:
        if (
            type(local_result) is not KnowledgeResolutionResult
            or local_result.handled is not True
            or local_result.success is not True
            or local_result.resolution_route != LOCAL_CAPABILITY_ROUTE
            or local_result.model_used is not False
            or local_result.external_access is not False
        ):
            raise TypeError(
                "Knowledge intent and local result are inconsistent."
            )

    @staticmethod
    def _require_knowledge_discovery_success(local_result) -> None:
        if (
            type(local_result) is not KnowledgeDiscoveryResolutionResult
            or local_result.handled is not True
            or local_result.success is not True
            or local_result.resolution_route != LOCAL_CAPABILITY_ROUTE
            or local_result.model_used is not False
            or local_result.external_access is not False
        ):
            raise TypeError(
                "Knowledge intent and local result are inconsistent."
            )

    @staticmethod
    def _map_knowledge_record(
        record: KnowledgeRecord,
    ) -> LocalKnowledgeRecordProjection:
        if type(record) is not KnowledgeRecord:
            raise TypeError("Knowledge record is inconsistent.")
        kind_map = {
            KnowledgeKind.FACT: LocalKnowledgeRecordKind.FACT,
            KnowledgeKind.CONCEPT: LocalKnowledgeRecordKind.CONCEPT,
            KnowledgeKind.STATE: LocalKnowledgeRecordKind.STATE,
        }
        if type(record.kind) is not KnowledgeKind or record.kind not in kind_map:
            raise TypeError("Knowledge record kind is inconsistent.")
        return LocalKnowledgeRecordProjection(
            record_id=record.record_id,
            kind=kind_map[record.kind],
            key=record.key,
            value=record.value,
        )

    @staticmethod
    def _validate_add_projection(
        intent: AddListItemsCommand,
        projection: LocalListAddProjection,
    ) -> None:
        if not projection.items:
            raise TypeError("Successful list add returned no final items.")
        if Counter(projection.added + projection.already_present) != Counter(
            intent.items
        ):
            raise TypeError("List add classifications are inconsistent.")
        if any(item not in projection.items for item in projection.added):
            raise TypeError("Added list item is absent from final items.")
        final_casefolded = {item.casefold() for item in projection.items}
        if any(
            item.casefold() not in final_casefolded
            for item in projection.already_present
        ):
            raise TypeError(
                "Already-present list item is absent from final items."
            )

    def _map_safe_insufficiency(
        self,
        reason,
    ) -> LocalCommandApplicationResult:
        if reason is SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED:
            return self._failure(
                LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED,
                LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            )

        if reason is SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID:
            return self._failure(
                LocalCommandApplicationErrorCode.INVALID_REQUEST,
                LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            )

        raise TypeError(
            "Safe-insufficiency result contains an unknown reason."
        )

    def _map_cognitive_result(
        self,
        outcome,
    ) -> LocalCommandApplicationResult:
        if outcome is None:
            raise TypeError(
                "Cognitive coordinated route omitted the outcome."
            )

        if outcome.success:
            return LocalCommandApplicationResult(
                True,
                route=LocalCommandApplicationRoute.COGNITIVE,
                response=outcome.response,
            )

        if (
            outcome.error is None
            or outcome.error.code not in COGNITIVE_ERROR_CODES
        ):
            raise TypeError(
                "Cognitive result contains an unknown failure."
            )

        return self._failure(
            LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED,
            LocalCommandApplicationRoute.COGNITIVE,
        )

    @staticmethod
    def _failure(
        code: LocalCommandApplicationErrorCode,
        route: LocalCommandApplicationRoute | None = None,
    ) -> LocalCommandApplicationResult:
        return LocalCommandApplicationResult(
            False,
            route=route,
            error=application_error(code),
        )
