"""Sequencing proofs for trusted local command routing."""

from dataclasses import FrozenInstanceError, fields
from unittest.mock import Mock

import pytest

import app.cognition.trusted_context as trusted_context
from app.cognition.domain.cognitive_outcome import CognitiveOutcome
from app.cognition.interpretation.interpreter import (
    DeterministicLocalCommandInterpreter,
)
from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.interpretation.routing import (
    LocalCommandTextRouter,
    TextRoutingRequest,
    TextRoutingResult,
)
from app.cognition.local_resolution.capability import StructuredListCapability
from app.cognition.local_resolution.knowledge_capability import (
    StructuredKnowledgeCapability,
)
from app.cognition.local_resolution.models import (
    LOCAL_PERMISSION_DENIED,
    ActorIdentity,
    WorkspaceIdentity,
)
from app.cognition.local_resolution.permissions import (
    LIST_ITEMS_ADD,
    ExplicitPermissionPolicy,
    PermissionGrant,
)
from app.cognition.local_resolution.repository import (
    InMemoryKnowledgeRecordRepository,
    InMemoryListItemRepository,
)
from app.cognition.local_resolution.resolver import LocalFirstResolver
from app.cognition.routing.coordinator import LocalFirstCognitiveCoordinator
from app.cognition.routing.models import (
    CognitiveFallbackAuthorization,
    CoordinatedRoute,
)
from app.cognition.trusted_context import (
    TRUSTED_CONTEXT_INVALID_INPUT,
    TRUSTED_CONTEXT_RESOLUTION_FAILED,
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
    TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
    TrustedHostRequestInput,
    TrustedLocalCommandRequest,
    TrustedLocalCommandRoutingService,
    TrustedRequestContext,
    TrustedRequestContextResolution,
)

ERROR_CODES = (
    TRUSTED_CONTEXT_INVALID_INPUT,
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
    TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
    TRUSTED_CONTEXT_RESOLUTION_FAILED,
)


def _context() -> TrustedRequestContext:
    return TrustedRequestContext(
        ActorIdentity("actor"),
        WorkspaceIdentity("workspace"),
    )


def _success() -> TrustedRequestContextResolution:
    return TrustedRequestContextResolution(True, _context())


def _failure(
    error_code: str = TRUSTED_CONTEXT_UNKNOWN_BINDING,
) -> TrustedRequestContextResolution:
    return TrustedRequestContextResolution(False, error_code=error_code)


def _request(text: object = "list add x :: a") -> TrustedLocalCommandRequest:
    return TrustedLocalCommandRequest(
        TrustedHostRequestInput("host-key", "workspace"),
        text,
        CognitiveFallbackAuthorization(False),
    )


def _text_result() -> TextRoutingResult:
    return TextRoutingResult(
        LocalCommandInterpretation(
            LocalCommandInterpretationStatus.INVALID,
            invalid_reason=LocalCommandInvalidReason.INVALID_INPUT,
        )
    )


def test_constructor_requires_both_collaborators() -> None:
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingService(None, Mock())
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingService(Mock(), None)
    TrustedLocalCommandRoutingService(Mock(), Mock())


class _FalseyResolver:
    def __bool__(self) -> bool:
        return False

    def resolve(self, request: TrustedHostRequestInput):
        return _failure()


class _FalseyRouter:
    def __init__(self) -> None:
        self.calls = 0

    def __bool__(self) -> bool:
        return False

    def route(self, request: TextRoutingRequest):
        self.calls += 1
        return _text_result()


def test_falsey_collaborators_are_retained_without_replacement() -> None:
    resolver = _FalseyResolver()
    router = _FalseyRouter()
    service = TrustedLocalCommandRoutingService(resolver, router)
    result = service.route(_request())
    assert result.trust_resolution.error_code == TRUSTED_CONTEXT_UNKNOWN_BINDING
    assert service._resolver is resolver
    assert service._router is router
    assert router.calls == 0


def test_wrong_request_type_raises_before_collaborator_calls() -> None:
    resolver = Mock()
    router = Mock()
    service = TrustedLocalCommandRoutingService(resolver, router)
    for request in (None, object(), TrustedHostRequestInput("key", "workspace")):
        with pytest.raises(TypeError):
            service.route(request)
    resolver.resolve.assert_not_called()
    router.route.assert_not_called()


def test_invalid_resolver_output_raises_and_stops_before_router() -> None:
    resolver = Mock()
    resolver.resolve.return_value = object()
    router = Mock()
    request = _request()
    with pytest.raises(TypeError):
        TrustedLocalCommandRoutingService(resolver, router).route(request)
    resolver.resolve.assert_called_once_with(request.host_input)
    router.route.assert_not_called()


@pytest.mark.parametrize("error_code", ERROR_CODES)
def test_each_trust_failure_is_preserved_and_short_circuits(error_code) -> None:
    resolution = _failure(error_code)
    resolver = Mock()
    resolver.resolve.return_value = resolution
    router = Mock()
    request = _request()
    result = TrustedLocalCommandRoutingService(resolver, router).route(request)
    assert result.trust_resolution is resolution
    assert result.text_routing_result is None
    resolver.resolve.assert_called_once_with(request.host_input)
    router.route.assert_not_called()


def test_success_builds_one_exact_request_and_preserves_result_identities() -> None:
    actor = ActorIdentity("actor")
    workspace = WorkspaceIdentity("workspace")
    resolution = TrustedRequestContextResolution(
        True,
        TrustedRequestContext(actor, workspace),
    )
    resolver = Mock()
    resolver.resolve.return_value = resolution
    router_result = _text_result()
    router = Mock()
    router.route.return_value = router_result
    text = object()
    request = _request(text)

    result = TrustedLocalCommandRoutingService(resolver, router).route(request)

    resolver.resolve.assert_called_once_with(request.host_input)
    router.route.assert_called_once()
    routed_request = router.route.call_args.args[0]
    assert type(routed_request) is TextRoutingRequest
    assert routed_request.actor is actor
    assert routed_request.workspace is workspace
    assert routed_request.text is text
    assert routed_request.fallback_authorization is request.fallback_authorization
    assert result.trust_resolution is resolution
    assert result.text_routing_result is router_result
    assert request.text is text
    with pytest.raises(FrozenInstanceError):
        request.text = "changed"


def test_invalid_router_output_raises_after_exactly_one_call_each() -> None:
    resolver = Mock()
    resolver.resolve.return_value = _success()
    router = Mock()
    router.route.return_value = object()
    with pytest.raises(TypeError):
        TrustedLocalCommandRoutingService(resolver, router).route(_request())
    resolver.resolve.assert_called_once()
    router.route.assert_called_once()


def test_trust_failure_has_zero_downstream_boundary_profile() -> None:
    resolution = _failure(TRUSTED_CONTEXT_RESOLUTION_FAILED)
    resolver = Mock()
    resolver.resolve.return_value = resolution
    boundaries = {
        name: Mock()
        for name in (
            "interpreter",
            "coordinator",
            "permission_policy",
            "repository",
            "model",
            "provider",
            "readiness",
            "network",
        )
    }
    router = Mock()
    router.boundaries = boundaries

    result = TrustedLocalCommandRoutingService(resolver, router).route(_request())

    assert result.trust_resolution is resolution
    router.route.assert_not_called()
    for boundary in boundaries.values():
        boundary.assert_not_called()


def _real_router(actions: tuple[str, ...] = (LIST_ITEMS_ADD,)):
    grants = (
        PermissionGrant("actor", "workspace", frozenset(actions)),
    ) if actions else ()
    policy = ExplicitPermissionPolicy(grants)
    repository = InMemoryListItemRepository()
    local_resolver = LocalFirstResolver(
        StructuredListCapability(repository, policy),
        StructuredKnowledgeCapability(InMemoryKnowledgeRecordRepository(), policy),
    )
    processor = Mock()
    processor.process.return_value = CognitiveOutcome(True, response="cognitive")
    coordinator = LocalFirstCognitiveCoordinator(local_resolver, processor)
    return (
        LocalCommandTextRouter(DeterministicLocalCommandInterpreter(), coordinator),
        repository,
        processor,
    )


def _service_with_real_router(router):
    resolver = Mock()
    resolver.resolve.return_value = _success()
    return TrustedLocalCommandRoutingService(resolver, router)


def test_real_router_preserves_local_success_and_permission_denial() -> None:
    permitted_router, repository, processor = _real_router()
    permitted = _service_with_real_router(permitted_router).route(_request())
    assert permitted.text_routing_result.coordinated_result.route is (
        CoordinatedRoute.LOCAL
    )
    assert repository.read(WorkspaceIdentity("workspace"), "x").items == ("a",)

    denied_router, denied_repository, denied_processor = _real_router(())
    denied = _service_with_real_router(denied_router).route(_request())
    local_result = denied.text_routing_result.coordinated_result.local_result
    assert denied.trust_resolution.success
    assert local_result.error_code == LOCAL_PERMISSION_DENIED
    assert denied_repository.read(WorkspaceIdentity("workspace"), "x").items == ()
    processor.process.assert_not_called()
    denied_processor.process.assert_not_called()


def test_workspace_payload_is_rejected_by_existing_interpreter() -> None:
    router, repository, processor = _real_router()
    text = (
        'knowledge store :: {"record_id":"r","kind":"fact","key":"k",'
        '"value":"v","source_type":"user","source_reference":"actor",'
        '"workspace":"other"}'
    )
    result = _service_with_real_router(router).route(_request(text))
    routed = result.text_routing_result
    assert routed.interpretation.status is LocalCommandInterpretationStatus.INVALID
    assert routed.interpretation.invalid_reason is (
        LocalCommandInvalidReason.INVALID_KNOWLEDGE_FIELDS
    )
    assert routed.coordinated_result is None
    assert repository.read(WorkspaceIdentity("workspace"), "x").items == ()
    processor.process.assert_not_called()


def test_result_has_no_sensitive_raw_or_duplicated_fields() -> None:
    resolver = Mock()
    resolver.resolve.return_value = _failure()
    result = TrustedLocalCommandRoutingService(resolver, Mock()).route(_request())
    assert tuple(field.name for field in fields(result)) == (
        "trust_resolution",
        "text_routing_result",
    )
    for name in (
        "binding_key",
        "requested_workspace_id",
        "permissions",
        "authentication",
        "session",
        "transport",
        "success",
    ):
        assert not hasattr(result, name)


def test_public_surface_exposes_service_but_no_container_or_demo() -> None:
    assert (
        trusted_context.TrustedLocalCommandRoutingService
        is TrustedLocalCommandRoutingService
    )
    assert "TrustedLocalCommandRoutingService" in trusted_context.__all__
    for name in ("Container", "TrustedRequestContextDemoRuntime"):
        assert name not in trusted_context.__all__
        assert not hasattr(trusted_context, name)
