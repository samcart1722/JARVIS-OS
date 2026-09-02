import ast
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from app.cognition.domain.cognitive_outcome import (
    CAPABILITY_EXECUTION_FAILED,
    CognitiveOutcome,
    cognitive_error,
)
from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.interpretation.routing import TextRoutingResult
from app.cognition.local_resolution.models import (
    LOCAL_CAPABILITY_ROUTE,
    LOCAL_KNOWLEDGE_CONFLICT,
    LOCAL_KNOWLEDGE_NOT_FOUND,
    LOCAL_PERMISSION_DENIED,
    LOCAL_VALIDATION_FAILED,
    ActorIdentity,
    AddListItemsCommand,
    FindKnowledgeRecordsQuery,
    KnowledgeDiscoveryResolutionResult,
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeResolutionResult,
    LocalResolutionResult,
    ReadKnowledgeRecordQuery,
    ReadListItemsQuery,
    StoreKnowledgeRecordCommand,
    WorkspaceIdentity,
)
from app.cognition.routing.models import (
    CoordinatedResult,
    CoordinatedRoute,
    SafeInsufficiencyReason,
)
from app.core.config import Settings
from app.core.container import Container
from app.local_command import (
    LOCAL_COMMAND_TEXT_MAX_LENGTH,
    WORKSPACE_ID_MAX_LENGTH,
    LocalCommandApplicationError,
    LocalCommandApplicationErrorCode,
    LocalCommandApplicationGateway,
    LocalCommandApplicationRequest,
    LocalCommandApplicationResult,
    LocalCommandApplicationRoute,
    LocalCommandProjectionKind,
    LocalKnowledgeFindProjection,
    LocalKnowledgeProjectionOperation,
    LocalKnowledgeReadProjection,
    LocalKnowledgeRecordKind,
    LocalKnowledgeStoreProjection,
    LocalListAddProjection,
    LocalListProjectionOperation,
    LocalListReadProjection,
    application_error,
)
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    MEMBERSHIP_NOT_FOUND,
    MEMBERSHIP_RESOLUTION_FAILED,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
)
from app.principal_authentication.models import (
    AuthenticatedPrincipal,
    LocalAuthenticationProof,
    PrincipalActorMappingErrorCode,
    PrincipalActorMappingResult,
    PrincipalAuthenticationErrorCode,
    PrincipalAuthenticationResult,
    PrincipalIdentity,
)
from app.principal_authentication.routing import (
    AuthenticatedLocalCommandRequest,
    AuthenticatedLocalCommandRoutingResult,
    AuthenticatedWorkspaceSelectionErrorCode,
    AuthenticatedWorkspaceSelectionResult,
)


def _request(**overrides) -> LocalCommandApplicationRequest:
    values = {
        "proof": "super-secret-proof",
        "requested_workspace_id": "workspace",
        "text": "list read groceries",
        "allow_cognitive_fallback": False,
    }
    values.update(overrides)
    return LocalCommandApplicationRequest(**values)



def _gateway(
    service: object,
) -> LocalCommandApplicationGateway:
    return LocalCommandApplicationGateway(
        cast(Any, service)
    )


def _application_error_code(
    result: LocalCommandApplicationResult,
) -> LocalCommandApplicationErrorCode:
    assert result.error is not None
    return result.error.code

def test_application_request_is_immutable_and_normalizes_workspace_only() -> None:
    request = _request(
        requested_workspace_id="  workspace  ",
        text="  list read groceries  ",
    )

    assert request.requested_workspace_id == "workspace"
    assert request.text == "  list read groceries  "

    with pytest.raises(AttributeError, match="immutable"):
        cast(Any, request).text = "changed"


def test_application_request_repr_never_contains_proof() -> None:
    proof = "proof-that-must-never-appear"
    request = _request(proof=proof)

    representation = repr(request)

    assert proof not in representation
    assert "proof=" not in representation


@pytest.mark.parametrize(
    "proof",
    (
        None,
        "",
        "   ",
    ),
)
def test_application_request_rejects_missing_or_blank_proof(proof) -> None:
    with pytest.raises(ValueError, match="proof"):
        _request(proof=proof)


@pytest.mark.parametrize(
    "workspace_id",
    (
        "",
        "   ",
        123,
        None,
    ),
)
def test_application_request_rejects_invalid_workspace(workspace_id) -> None:
    with pytest.raises(ValueError, match="Workspace"):
        _request(requested_workspace_id=workspace_id)


def test_application_request_rejects_oversized_workspace() -> None:
    with pytest.raises(ValueError, match="too long"):
        _request(
            requested_workspace_id="w" * (WORKSPACE_ID_MAX_LENGTH + 1),
        )


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        123,
        None,
    ),
)
def test_application_request_rejects_invalid_text(text) -> None:
    with pytest.raises(ValueError, match="command text"):
        _request(text=text)


def test_application_request_rejects_oversized_text() -> None:
    with pytest.raises(ValueError, match="too long"):
        _request(
            text="x" * (LOCAL_COMMAND_TEXT_MAX_LENGTH + 1),
        )


@pytest.mark.parametrize(
    "fallback",
    (
        0,
        1,
        "false",
        "true",
        None,
    ),
)
def test_application_request_requires_strict_fallback_boolean(fallback) -> None:
    with pytest.raises(ValueError, match="explicit boolean"):
        _request(allow_cognitive_fallback=fallback)


@pytest.mark.parametrize(
    "fallback",
    (
        False,
        True,
    ),
)
def test_application_request_accepts_explicit_fallback_boolean(fallback) -> None:
    request = _request(allow_cognitive_fallback=fallback)

    assert request.allow_cognitive_fallback is fallback


@pytest.mark.parametrize(
    "code",
    tuple(LocalCommandApplicationErrorCode),
)
def test_application_error_factory_produces_canonical_closed_errors(code) -> None:
    error = application_error(code)

    assert error.code is code
    assert error.message


def test_local_validation_failure_message_is_non_blaming() -> None:
    error = application_error(
        LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED
    )

    assert error.message == "The local operation could not be completed."
    assert "invalid" not in error.message.lower()


def test_application_error_rejects_noncanonical_message() -> None:
    with pytest.raises(ValueError, match="canonical"):
        LocalCommandApplicationError(
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
            "Wrong message.",
        )


@pytest.mark.parametrize(
    "route",
    (
        LocalCommandApplicationRoute.LOCAL,
        LocalCommandApplicationRoute.COGNITIVE,
    ),
)
def test_successful_application_result_requires_usable_route(route) -> None:
    result = LocalCommandApplicationResult(
        True,
        route=route,
        response="completed",
    )

    assert result.success
    assert result.route is route
    assert result.response == "completed"
    assert result.error is None


def test_successful_application_result_rejects_safe_insufficiency() -> None:
    with pytest.raises(ValueError, match="usable route"):
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            response="completed",
        )


@pytest.mark.parametrize(
    "response",
    (
        None,
        "",
        "   ",
    ),
)
def test_successful_application_result_requires_nonblank_response(response) -> None:
    with pytest.raises(ValueError, match="requires a response"):
        LocalCommandApplicationResult(
            True,
            route=LocalCommandApplicationRoute.LOCAL,
            response=response,
        )


def test_failed_application_result_allows_precoordination_route_none() -> None:
    error = application_error(
        LocalCommandApplicationErrorCode.ACCESS_DENIED
    )

    result = LocalCommandApplicationResult(
        False,
        error=error,
    )

    assert not result.success
    assert result.route is None
    assert result.response is None
    assert result.error is error


def test_failed_application_result_allows_safe_insufficiency_route() -> None:
    error = application_error(
        LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED
    )

    result = LocalCommandApplicationResult(
        False,
        route=LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
        error=error,
    )

    assert not result.success
    assert result.route is LocalCommandApplicationRoute.SAFE_INSUFFICIENCY
    assert result.response is None
    assert result.error is error


def test_failed_application_result_requires_error() -> None:
    with pytest.raises(ValueError, match="requires an application error"):
        LocalCommandApplicationResult(False)


def test_failed_application_result_forbids_response() -> None:
    with pytest.raises(ValueError, match="forbids a response"):
        LocalCommandApplicationResult(
            False,
            response="should not exist",
            error=application_error(
                LocalCommandApplicationErrorCode.INTERNAL_ERROR
            ),
        )

class RecordingRoutingService:
    def __init__(self, result) -> None:
        self.result = result
        self.requests = []

    def route(self, request):
        self.requests.append(request)
        return self.result


def _authentication_success() -> PrincipalAuthenticationResult:
    return PrincipalAuthenticationResult(
        True,
        AuthenticatedPrincipal(
            PrincipalIdentity("principal")
        ),
    )


def _mapping_success() -> PrincipalActorMappingResult:
    return PrincipalActorMappingResult(
        True,
        ActorIdentity("actor"),
    )


def _selection_success(
    workspace: WorkspaceIdentity | None = None,
) -> AuthenticatedWorkspaceSelectionResult:
    return AuthenticatedWorkspaceSelectionResult(
        True,
        workspace or WorkspaceIdentity("workspace"),
    )


def _membership_success(
    workspace: WorkspaceIdentity | None = None,
) -> MembershipDecision:
    return MembershipDecision(
        True,
        ActorWorkspaceMembership(
            ActorIdentity("actor"),
            workspace or WorkspaceIdentity("workspace"),
            MembershipStatus.ACTIVE,
        ),
    )


def _interpreted(intent=None) -> LocalCommandInterpretation:
    return LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INTERPRETED,
        intent if intent is not None else ReadListItemsQuery("groceries"),
    )


def _not_interpreted() -> LocalCommandInterpretation:
    return LocalCommandInterpretation(
        LocalCommandInterpretationStatus.NOT_INTERPRETED
    )


def _full_result(
    text_routing: TextRoutingResult,
    workspace: WorkspaceIdentity | None = None,
) -> AuthenticatedLocalCommandRoutingResult:
    selected_workspace = workspace or WorkspaceIdentity("workspace")
    return AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        _mapping_success(),
        _selection_success(selected_workspace),
        _membership_success(selected_workspace),
        text_routing,
    )


def _local_text_result(
    *,
    success: bool,
    response: str,
    error_code: str | None = None,
    intent=None,
    added: tuple[str, ...] = (),
    already_present: tuple[str, ...] = (),
    items: tuple[str, ...] = (),
) -> TextRoutingResult:
    local_result = LocalResolutionResult(
        True,
        success,
        response,
        LOCAL_CAPABILITY_ROUTE,
        added=added,
        already_present=already_present,
        items=items,
        error_code=error_code,
    )
    return TextRoutingResult(
        _interpreted(intent),
        CoordinatedResult(
            CoordinatedRoute.LOCAL,
            local_result=local_result,
        ),
    )


def test_gateway_constructs_one_internal_authenticated_request() -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        PrincipalAuthenticationResult(
            False,
            error_code=(
                PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED
            ),
        )
    )
    service = RecordingRoutingService(routed)
    gateway = _gateway(service)
    proof = "proof-that-must-remain-secret"

    result = gateway.execute(
        _request(
            proof=proof,
            allow_cognitive_fallback=True,
        )
    )

    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.ACCESS_DENIED
    )
    assert len(service.requests) == 1

    internal = service.requests[0]

    assert type(internal) is AuthenticatedLocalCommandRequest
    assert type(internal.authentication_proof) is LocalAuthenticationProof
    assert internal.authentication_proof.proof == proof
    assert internal.requested_workspace_id == "workspace"
    assert internal.text == "list read groceries"
    assert internal.fallback_authorization.allowed is True
    assert proof not in repr(internal.authentication_proof)
    assert proof not in repr(internal)


def test_gateway_rejects_invalid_application_request_without_routing() -> None:
    service = RecordingRoutingService(object())
    gateway = _gateway(service)

    with pytest.raises(TypeError, match="application request"):
        gateway.execute(cast(Any, object()))

    assert service.requests == []


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            PrincipalAuthenticationErrorCode.AUTHENTICATION_FAILED,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            PrincipalAuthenticationErrorCode.AUTHENTICATION_RESOLUTION_FAILED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
        ),
    ),
)
def test_gateway_maps_authentication_failures(
    internal_code,
    expected,
) -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        PrincipalAuthenticationResult(
            False,
            error_code=internal_code,
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert _application_error_code(result) is expected


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_FAILED,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            PrincipalActorMappingErrorCode.PRINCIPAL_MAPPING_RESOLUTION_FAILED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
        ),
    ),
)
def test_gateway_maps_principal_mapping_failures(
    internal_code,
    expected,
) -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        PrincipalActorMappingResult(
            False,
            error_code=internal_code,
        ),
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert _application_error_code(result) is expected


def test_gateway_maps_invalid_workspace_selection() -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        _mapping_success(),
        AuthenticatedWorkspaceSelectionResult(
            False,
            error_code=(
                AuthenticatedWorkspaceSelectionErrorCode.WORKSPACE_SELECTION_INVALID
            ),
        ),
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.INVALID_REQUEST
    )


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            MEMBERSHIP_NOT_FOUND,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            MEMBERSHIP_INACTIVE,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            MEMBERSHIP_RESOLUTION_FAILED,
            LocalCommandApplicationErrorCode.SERVICE_UNAVAILABLE,
        ),
    ),
)
def test_gateway_maps_membership_failures(
    internal_code,
    expected,
) -> None:
    routed = AuthenticatedLocalCommandRoutingResult(
        _authentication_success(),
        _mapping_success(),
        _selection_success(),
        MembershipDecision(
            False,
            error_code=internal_code,
        ),
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert _application_error_code(result) is expected


def test_gateway_maps_invalid_interpretation_to_invalid_request() -> None:
    interpretation = LocalCommandInterpretation(
        LocalCommandInterpretationStatus.INVALID,
        invalid_reason=LocalCommandInvalidReason.INVALID_INPUT,
    )
    routed = _full_result(
        TextRoutingResult(interpretation)
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.INVALID_REQUEST
    )


def test_gateway_maps_local_success() -> None:
    routed = _full_result(
        _local_text_result(
            success=True,
            response="List read locally.",
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert result.response == "List read locally."
    assert result.error is None


def _execute_successful_local(
    intent,
    local_result,
    workspace: WorkspaceIdentity | None = None,
):
    routed = _full_result(
        TextRoutingResult(
            _interpreted(intent),
            CoordinatedResult(
                CoordinatedRoute.LOCAL,
                local_result=local_result,
            ),
        ),
        workspace,
    )
    return _gateway(RecordingRoutingService(routed)).execute(_request())


def _list_success(
    response: str,
    *,
    added: tuple[str, ...] = (),
    already_present: tuple[str, ...] = (),
    items: tuple[str, ...] = (),
    handled: bool = True,
    route: str = LOCAL_CAPABILITY_ROUTE,
) -> LocalResolutionResult:
    return LocalResolutionResult(
        handled,
        True,
        response,
        route,
        added=added,
        already_present=already_present,
        items=items,
    )


@pytest.mark.parametrize(
    ("intent_items", "added", "already_present", "items"),
    (
        (("alpha", "beta"), ("alpha", "beta"), (), ("alpha", "beta")),
        (("alpha", "beta"), (), ("alpha", "beta"), ("alpha", "beta")),
        (("alpha", "alpha"), ("alpha",), ("alpha",), ("alpha",)),
        (
            ("alpha", "beta", "alpha", "gamma", "beta"),
            ("alpha", "beta", "gamma"),
            ("alpha", "beta"),
            ("prior", "alpha", "beta", "gamma"),
        ),
        (("alpha",), (), ("alpha",), ("ALPHA",)),
    ),
)
def test_gateway_maps_valid_add_classifications_without_rewriting(
    intent_items,
    added,
    already_present,
    items,
) -> None:
    intent = AddListItemsCommand("groceries", intent_items)
    result = _execute_successful_local(
        intent,
        _list_success(
            "List updated locally.",
            added=added,
            already_present=already_present,
            items=items,
        ),
    )

    assert result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert result.response == "List updated locally."
    assert result.error is None
    assert type(result.projection) is LocalListAddProjection
    assert result.projection == LocalListAddProjection(
        list_id="groceries",
        added=added,
        already_present=already_present,
        items=items,
    )
    assert result.projection.kind is LocalCommandProjectionKind.LIST
    assert result.projection.operation is LocalListProjectionOperation.ADD


@pytest.mark.parametrize(
    ("added", "already_present", "items"),
    (
        (("alpha",), (), ("alpha",)),
        (("alpha", "beta", "extra"), (), ("alpha", "beta", "extra")),
        (("alpha", "beta"), (), ()),
        (("alpha", "beta"), (), ("alpha",)),
        ((), ("alpha", "beta"), ("alpha",)),
    ),
)
def test_gateway_fails_closed_for_inconsistent_add_result(
    added,
    already_present,
    items,
) -> None:
    intent = AddListItemsCommand("groceries", ("alpha", "beta"))

    with pytest.raises(TypeError):
        _execute_successful_local(
            intent,
            _list_success(
                "List updated locally.",
                added=added,
                already_present=already_present,
                items=items,
            ),
        )


@pytest.mark.parametrize(
    "local_result",
    (
        _list_success(
            "List updated locally.",
            added=("alpha",),
            items=("alpha",),
            route="wrong_route",
        ),
        KnowledgeDiscoveryResolutionResult(
            True,
            True,
            "Knowledge records found locally.",
            LOCAL_CAPABILITY_ROUTE,
        ),
    ),
)
def test_gateway_requires_exact_successful_list_result_contract(local_result) -> None:
    with pytest.raises(TypeError):
        _execute_successful_local(
            AddListItemsCommand("groceries", ("alpha",)),
            local_result,
        )


@pytest.mark.parametrize("items", (("beta", "alpha"), ()))
def test_gateway_maps_read_projection_preserving_order_and_empty(items) -> None:
    result = _execute_successful_local(
        ReadListItemsQuery("groceries"),
        _list_success("List read locally.", items=items),
    )

    assert result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert result.response == "List read locally."
    assert result.error is None
    assert result.projection == LocalListReadProjection("groceries", items)
    assert result.projection.operation is LocalListProjectionOperation.READ


@pytest.mark.parametrize(
    ("added", "already_present"),
    ((('unexpected',), ()), ((), ('unexpected',))),
)
def test_gateway_fails_closed_for_read_classification_contamination(
    added,
    already_present,
) -> None:
    with pytest.raises(TypeError, match="classification"):
        _execute_successful_local(
            ReadListItemsQuery("groceries"),
            _list_success(
                "List read locally.",
                added=added,
                already_present=already_present,
            ),
        )


def _knowledge_record(
    record_id: str = "record",
    *,
    workspace: str = "workspace",
    kind: KnowledgeKind = KnowledgeKind.FACT,
    key: str = "key",
    value: str = "value",
    source_reference: str = "gateway",
) -> KnowledgeRecord:
    return KnowledgeRecord(
        record_id,
        WorkspaceIdentity(workspace),
        kind,
        key,
        value,
        KnowledgeProvenance("test", source_reference),
    )


@pytest.mark.parametrize("created", (True, False))
def test_gateway_maps_store_projection_and_preserves_response(created) -> None:
    record = _knowledge_record()
    result = _execute_successful_local(
        StoreKnowledgeRecordCommand(record),
        KnowledgeResolutionResult(
            True, True, "canonical store", LOCAL_CAPABILITY_ROUTE,
            record=record, created=created,
        ),
    )

    assert result.response == "canonical store"
    assert type(result.projection) is LocalKnowledgeStoreProjection
    assert result.projection.kind is LocalCommandProjectionKind.KNOWLEDGE
    assert result.projection.operation is LocalKnowledgeProjectionOperation.STORE
    assert result.projection.created is created
    assert (
        result.projection.record.record_id,
        result.projection.record.kind,
        result.projection.record.key,
        result.projection.record.value,
    ) == ("record", LocalKnowledgeRecordKind.FACT, "key", "value")
    assert not hasattr(result.projection.record, "workspace")
    assert not hasattr(result.projection.record, "provenance")


def test_gateway_imports_no_execution_or_storage_authority() -> None:
    gateway_path = Path(__file__).parents[3] / "app/local_command/gateway.py"
    tree = ast.parse(gateway_path.read_text(encoding="utf-8"))
    prohibited_prefixes = (
        "app.cognition.local_resolution.repository",
        "app.cognition.local_resolution.knowledge_capability",
        "app.cognition.local_resolution.resolver",
        "app.infrastructure.local_storage",
        "app.core.container",
    )
    imported_modules = {
        module
        for node in ast.walk(tree)
        for module in (
            (
                node.module
                if isinstance(node, ast.ImportFrom)
                else alias.name
            )
            for alias in (
                node.names
                if isinstance(node, (ast.Import, ast.ImportFrom))
                else ()
            )
        )
        if module is not None
    }
    prohibited_imports = {
        module
        for module in imported_modules
        if any(
            module == prefix or module.startswith(f"{prefix}.")
            for prefix in prohibited_prefixes
        )
    }

    assert prohibited_imports == set()


@pytest.mark.parametrize(
    "local_result",
    (
        KnowledgeDiscoveryResolutionResult(
            True, True, "wrong", LOCAL_CAPABILITY_ROUTE
        ),
        LocalResolutionResult(True, True, "wrong", LOCAL_CAPABILITY_ROUTE),
    ),
)
def test_gateway_store_rejects_wrong_result_type(local_result) -> None:
    with pytest.raises(TypeError, match="Knowledge"):
        _execute_successful_local(
            StoreKnowledgeRecordCommand(_knowledge_record()), local_result
        )


@pytest.mark.parametrize(
    "returned",
    (
        _knowledge_record(workspace="other"),
        _knowledge_record(value="different"),
        _knowledge_record(source_reference="different-provenance"),
    ),
)
def test_gateway_store_rejects_workspace_record_and_provenance_mismatch(
    returned,
) -> None:
    intent_record = _knowledge_record()
    with pytest.raises(TypeError, match="store"):
        _execute_successful_local(
            StoreKnowledgeRecordCommand(intent_record),
            KnowledgeResolutionResult(
                True, True, "stored", LOCAL_CAPABILITY_ROUTE,
                record=returned, created=True,
            ),
        )


def test_gateway_store_rejects_selected_workspace_and_non_bool_created() -> None:
    record = _knowledge_record()
    result = KnowledgeResolutionResult(
        True, True, "stored", LOCAL_CAPABILITY_ROUTE,
        record=record, created=True,
    )
    with pytest.raises(TypeError, match="store"):
        _execute_successful_local(
            StoreKnowledgeRecordCommand(record), result,
            WorkspaceIdentity("other"),
        )
    object.__setattr__(result, "created", 1)
    with pytest.raises(TypeError, match="store"):
        _execute_successful_local(StoreKnowledgeRecordCommand(record), result)


def test_gateway_rejects_unknown_internal_knowledge_kind() -> None:
    record = _knowledge_record()
    object.__setattr__(record, "kind", "unknown")
    result = KnowledgeResolutionResult(
        True, True, "stored", LOCAL_CAPABILITY_ROUTE,
        record=record, created=True,
    )
    with pytest.raises(TypeError, match="kind"):
        _execute_successful_local(StoreKnowledgeRecordCommand(record), result)


def test_gateway_maps_read_projection_without_created() -> None:
    record = _knowledge_record(kind=KnowledgeKind.CONCEPT)
    result = _execute_successful_local(
        ReadKnowledgeRecordQuery("record"),
        KnowledgeResolutionResult(
            True, True, "canonical read", LOCAL_CAPABILITY_ROUTE,
            record=record,
        ),
    )

    assert result.response == "canonical read"
    assert type(result.projection) is LocalKnowledgeReadProjection
    assert result.projection.operation is LocalKnowledgeProjectionOperation.READ
    assert result.projection.record.kind is LocalKnowledgeRecordKind.CONCEPT
    assert result.projection.record.record_id == "record"
    assert not hasattr(result.projection, "created")


@pytest.mark.parametrize(
    "local_result",
    (
        KnowledgeDiscoveryResolutionResult(
            True, True, "wrong", LOCAL_CAPABILITY_ROUTE
        ),
        LocalResolutionResult(True, True, "wrong", LOCAL_CAPABILITY_ROUTE),
    ),
)
def test_gateway_read_rejects_wrong_result_type(local_result) -> None:
    with pytest.raises(TypeError, match="Knowledge"):
        _execute_successful_local(ReadKnowledgeRecordQuery("record"), local_result)


@pytest.mark.parametrize(
    "record",
    (
        _knowledge_record("other"),
        _knowledge_record(workspace="other"),
    ),
)
def test_gateway_read_rejects_id_and_workspace_mismatch(record) -> None:
    with pytest.raises(TypeError, match="read"):
        _execute_successful_local(
            ReadKnowledgeRecordQuery("record"),
            KnowledgeResolutionResult(
                True, True, "read", LOCAL_CAPABILITY_ROUTE, record=record
            ),
        )


@pytest.mark.parametrize("created", (True, 1))
def test_gateway_read_rejects_created_values(created) -> None:
    record = _knowledge_record()
    local_result = KnowledgeResolutionResult(
        True, True, "read", LOCAL_CAPABILITY_ROUTE, record=record
    )
    object.__setattr__(local_result, "created", created)
    with pytest.raises(TypeError, match="read"):
        _execute_successful_local(ReadKnowledgeRecordQuery("record"), local_result)


def _discovery_result(
    records: tuple[KnowledgeRecord, ...] = (),
    *,
    truncated: bool = False,
    response: str = "canonical find",
) -> KnowledgeDiscoveryResolutionResult:
    return KnowledgeDiscoveryResolutionResult(
        True, True, response, LOCAL_CAPABILITY_ROUTE,
        records=records, truncated=truncated,
    )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("handled", False),
        ("success", 1),
        ("resolution_route", "wrong_route"),
        ("model_used", True),
        ("external_access", True),
    ),
)
@pytest.mark.parametrize("result_family", ("resolution", "discovery"))
def test_gateway_rejects_corrupted_common_knowledge_success_fields(
    field_name,
    invalid_value,
    result_family,
) -> None:
    record = _knowledge_record()
    if result_family == "resolution":
        intent = ReadKnowledgeRecordQuery(record.record_id)
        local_result = KnowledgeResolutionResult(
            True, True, "read", LOCAL_CAPABILITY_ROUTE, record=record
        )
    else:
        intent = FindKnowledgeRecordsQuery(record.key)
        local_result = _discovery_result((record,))
    routed = _full_result(
        TextRoutingResult(
            _interpreted(intent),
            CoordinatedResult(
                CoordinatedRoute.LOCAL,
                local_result=local_result,
            ),
        )
    )
    object.__setattr__(local_result, field_name, invalid_value)

    with pytest.raises(TypeError, match="Knowledge"):
        _gateway(RecordingRoutingService(routed)).execute(_request())


@pytest.mark.parametrize(
    ("count", "truncated"),
    ((0, False), (1, False), (50, False), (50, True)),
)
def test_gateway_maps_find_boundaries(count, truncated) -> None:
    records = tuple(_knowledge_record(f"record-{index}") for index in range(count))
    result = _execute_successful_local(
        FindKnowledgeRecordsQuery("key"),
        _discovery_result(records, truncated=truncated),
    )

    assert result.response == "canonical find"
    assert type(result.projection) is LocalKnowledgeFindProjection
    assert result.projection.operation is LocalKnowledgeProjectionOperation.FIND
    assert tuple(record.record_id for record in result.projection.records) == tuple(
        record.record_id for record in records
    )
    assert result.projection.truncated is truncated


def test_gateway_find_preserves_order_and_correlates_optional_kind() -> None:
    records = (
        _knowledge_record("second", kind=KnowledgeKind.STATE),
        _knowledge_record("first", kind=KnowledgeKind.STATE),
    )
    result = _execute_successful_local(
        FindKnowledgeRecordsQuery("key", KnowledgeKind.STATE),
        _discovery_result(records),
    )

    assert tuple(record.record_id for record in result.projection.records) == (
        "second", "first"
    )
    assert all(
        record.kind is LocalKnowledgeRecordKind.STATE
        for record in result.projection.records
    )


@pytest.mark.parametrize(
    "records",
    (
        (_knowledge_record(workspace="other"),),
        (_knowledge_record(key="other"),),
        (_knowledge_record(kind=KnowledgeKind.CONCEPT),),
    ),
)
def test_gateway_find_rejects_workspace_key_and_requested_kind(records) -> None:
    with pytest.raises(TypeError, match="find"):
        _execute_successful_local(
            FindKnowledgeRecordsQuery("key", KnowledgeKind.FACT),
            _discovery_result(records),
        )


def test_gateway_find_rejects_wrong_type_duplicates_and_invalid_truncation() -> None:
    with pytest.raises(TypeError, match="Knowledge"):
        _execute_successful_local(
            FindKnowledgeRecordsQuery("key"),
            KnowledgeResolutionResult(
                True, True, "wrong", LOCAL_CAPABILITY_ROUTE,
                record=_knowledge_record(),
            ),
        )
    record = _knowledge_record()
    with pytest.raises(TypeError, match="find"):
        _execute_successful_local(
            FindKnowledgeRecordsQuery("key"),
            _discovery_result((record, record)),
        )
    local_result = _discovery_result()
    object.__setattr__(local_result, "truncated", 0)
    with pytest.raises(TypeError, match="find"):
        _execute_successful_local(FindKnowledgeRecordsQuery("key"), local_result)


def test_gateway_find_rejects_missing_workspace_unknown_kind_and_too_many() -> None:
    query = FindKnowledgeRecordsQuery("key")
    with pytest.raises(TypeError, match="selected workspace"):
        LocalCommandApplicationGateway._map_local_success_projection(
            query, _discovery_result(), None
        )
    object.__setattr__(query, "kind", "unknown")
    with pytest.raises(TypeError, match="find"):
        _execute_successful_local(query, _discovery_result())
    local_result = _discovery_result()
    object.__setattr__(
        local_result,
        "records",
        tuple(_knowledge_record(f"record-{index}") for index in range(51)),
    )
    with pytest.raises(TypeError, match="find"):
        _execute_successful_local(FindKnowledgeRecordsQuery("key"), local_result)


def test_gateway_uses_selected_workspace_without_reparsing_request_text() -> None:
    record = _knowledge_record()
    routed = _full_result(
        TextRoutingResult(
            _interpreted(ReadKnowledgeRecordQuery("record")),
            CoordinatedResult(
                CoordinatedRoute.LOCAL,
                local_result=KnowledgeResolutionResult(
                    True, True, "read", LOCAL_CAPABILITY_ROUTE, record=record
                ),
            ),
        )
    )
    service = RecordingRoutingService(routed)
    result = _gateway(service).execute(_request(text="not parseable knowledge text"))

    assert result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert type(result.projection) is LocalKnowledgeReadProjection
    assert len(service.requests) == 1


def test_gateway_fails_closed_for_unknown_successful_local_intent() -> None:
    with pytest.raises(TypeError, match="unknown intent"):
        LocalCommandApplicationGateway._map_local_success_projection(
            object(),
            _list_success("Unexpected local success.", items=("alpha",)),
            WorkspaceIdentity("workspace"),
        )


@pytest.mark.parametrize(
    ("internal_code", "expected"),
    (
        (
            LOCAL_PERMISSION_DENIED,
            LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED,
        ),
        (
            LOCAL_VALIDATION_FAILED,
            LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED,
        ),
        (
            LOCAL_KNOWLEDGE_NOT_FOUND,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND,
        ),
        (
            LOCAL_KNOWLEDGE_CONFLICT,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_CONFLICT,
        ),
    ),
)
def test_gateway_maps_known_local_failures(
    internal_code,
    expected,
) -> None:
    routed = _full_result(
        _local_text_result(
            success=False,
            response="Local operation failed.",
            error_code=internal_code,
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert result.route is LocalCommandApplicationRoute.LOCAL
    assert result.response is None
    assert result.projection is None
    assert _application_error_code(result) is expected


@pytest.mark.parametrize(
    ("reason", "expected"),
    (
        (
            SafeInsufficiencyReason.FALLBACK_NOT_AUTHORIZED,
            LocalCommandApplicationErrorCode.COGNITIVE_FALLBACK_NOT_AUTHORIZED,
        ),
        (
            SafeInsufficiencyReason.COGNITIVE_INPUT_INVALID,
            LocalCommandApplicationErrorCode.INVALID_REQUEST,
        ),
    ),
)
def test_gateway_maps_safe_insufficiency(
    reason,
    expected,
) -> None:
    routed = _full_result(
        TextRoutingResult(
            _not_interpreted(),
            CoordinatedResult(
                CoordinatedRoute.SAFE_INSUFFICIENCY,
                insufficiency_reason=reason,
            ),
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(_request())

    assert not result.success
    assert (
        result.route
        is LocalCommandApplicationRoute.SAFE_INSUFFICIENCY
    )
    assert result.projection is None
    assert _application_error_code(result) is expected


def test_gateway_maps_cognitive_success() -> None:
    routed = _full_result(
        TextRoutingResult(
            _not_interpreted(),
            CoordinatedResult(
                CoordinatedRoute.COGNITIVE,
                cognitive_outcome=CognitiveOutcome(
                    True,
                    response="Cognitive answer.",
                ),
            ),
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(
        _request(allow_cognitive_fallback=True)
    )

    assert result.success
    assert result.route is LocalCommandApplicationRoute.COGNITIVE
    assert result.response == "Cognitive answer."
    assert result.error is None
    assert result.projection is None


def test_gateway_collapses_controlled_cognitive_failure() -> None:
    routed = _full_result(
        TextRoutingResult(
            _not_interpreted(),
            CoordinatedResult(
                CoordinatedRoute.COGNITIVE,
                cognitive_outcome=CognitiveOutcome(
                    False,
                    error=cognitive_error(
                        CAPABILITY_EXECUTION_FAILED
                    ),
                ),
            ),
        )
    )

    result = _gateway(RecordingRoutingService(routed)).execute(
        _request(allow_cognitive_fallback=True)
    )

    assert not result.success
    assert result.route is LocalCommandApplicationRoute.COGNITIVE
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.COGNITIVE_REQUEST_FAILED
    )


def test_gateway_rejects_invalid_routing_result_type() -> None:
    gateway = _gateway(RecordingRoutingService(object()))

    with pytest.raises(
        TypeError,
        match="invalid result",
    ):
        gateway.execute(_request())


def test_gateway_rejects_unknown_local_failure() -> None:
    routed = _full_result(
        _local_text_result(
            success=False,
            response="Local operation failed.",
            error_code="unknown_local_failure",
        )
    )

    gateway = _gateway(RecordingRoutingService(routed))

    with pytest.raises(
        TypeError,
        match="unknown failure",
    ):
        gateway.execute(_request())

def test_application_request_has_no_generic_dataclass_serialization() -> None:
    proof = "proof-that-must-never-serialize"
    request = _request(proof=proof)

    with pytest.raises(TypeError):
        asdict(cast(Any, request))

    with pytest.raises(TypeError):
        vars(request)

    assert not hasattr(request, "__dict__")


@pytest.mark.parametrize(
    "protocol",
    range(pickle.HIGHEST_PROTOCOL + 1),
)
def test_application_request_rejects_pickle_serialization(
    protocol: int,
) -> None:
    proof = "proof-that-must-never-be-pickled"
    request = _request(proof=proof)

    with pytest.raises(TypeError) as exc_info:
        pickle.dumps(
            request,
            protocol=protocol,
        )

    message = str(exc_info.value)

    assert "serialization is prohibited" in message
    assert proof not in message
    assert proof not in repr(exc_info.value)


@pytest.mark.parametrize(
    ("route", "code"),
    (
        (
            LocalCommandApplicationRoute.LOCAL,
            LocalCommandApplicationErrorCode.ACCESS_DENIED,
        ),
        (
            LocalCommandApplicationRoute.COGNITIVE,
            LocalCommandApplicationErrorCode.LOCAL_VALIDATION_FAILED,
        ),
        (
            LocalCommandApplicationRoute.SAFE_INSUFFICIENCY,
            LocalCommandApplicationErrorCode.LOCAL_PERMISSION_DENIED,
        ),
        (
            None,
            LocalCommandApplicationErrorCode.LOCAL_KNOWLEDGE_NOT_FOUND,
        ),
    ),
)
def test_failed_application_result_rejects_incoherent_route_error_pair(
    route,
    code,
) -> None:
    with pytest.raises(
        ValueError,
        match="route and error are inconsistent",
    ):
        LocalCommandApplicationResult(
            False,
            route=route,
            error=application_error(code),
        )


def test_internal_error_is_valid_only_before_route_classification() -> None:
    result = LocalCommandApplicationResult(
        False,
        error=application_error(
            LocalCommandApplicationErrorCode.INTERNAL_ERROR
        ),
    )

    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.INTERNAL_ERROR
    )

def test_container_composes_one_application_gateway_from_authenticated_route() -> None:
    container = Container(cast(Any, Settings)(_env_file=None))

    gateway = container.local_command_application_gateway

    assert type(gateway) is LocalCommandApplicationGateway
    assert (
        gateway._routing_service
        is container.authenticated_local_command_routing_service
    )


def test_default_container_application_gateway_fails_closed_before_downstream() -> None:
    container = Container(cast(Any, Settings)(_env_file=None))

    with (
        patch(
            "app.principal_authentication.configured_mapper."
            "ConfiguredPrincipalActorMapper.map"
        ) as map_principal,
        patch(
            "app.membership.service."
            "MembershipDecisionService.decide"
        ) as decide_membership,
        patch(
            "app.cognition.interpretation.routing."
            "LocalCommandTextRouter.route"
        ) as route_text,
    ):
        result = container.local_command_application_gateway.execute(
            _request()
        )

    assert not result.success
    assert result.route is None
    assert (
        _application_error_code(result)
        is LocalCommandApplicationErrorCode.ACCESS_DENIED
    )

    map_principal.assert_not_called()
    decide_membership.assert_not_called()
    route_text.assert_not_called()
