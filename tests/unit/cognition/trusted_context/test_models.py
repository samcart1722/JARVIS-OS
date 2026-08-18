"""Contract proofs for immutable trusted request context values."""

from dataclasses import FrozenInstanceError, fields

import pytest

import app.cognition.trusted_context as trusted_context
import app.cognition.trusted_context.models as trusted_models
from app.cognition.interpretation.models import (
    LocalCommandInterpretation,
    LocalCommandInterpretationStatus,
    LocalCommandInvalidReason,
)
from app.cognition.interpretation.routing import TextRoutingResult
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.routing.models import CognitiveFallbackAuthorization
from app.cognition.trusted_context import (
    TRUSTED_CONTEXT_INVALID_INPUT,
    TRUSTED_CONTEXT_RESOLUTION_FAILED,
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
    TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
    ConfiguredTrustedHostBinding,
    TrustedHostRequestInput,
    TrustedLocalCommandRequest,
    TrustedLocalCommandRoutingResult,
    TrustedRequestContext,
    TrustedRequestContextResolution,
    TrustedRequestContextResolver,
)
from app.membership.models import (
    MEMBERSHIP_INACTIVE,
    ActorWorkspaceMembership,
    MembershipDecision,
    MembershipStatus,
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


def _successful_resolution() -> TrustedRequestContextResolution:
    return TrustedRequestContextResolution(True, _context())


def _failed_resolution() -> TrustedRequestContextResolution:
    return TrustedRequestContextResolution(False, error_code=ERROR_CODES[0])


def _routing_result() -> TextRoutingResult:
    return TextRoutingResult(
        LocalCommandInterpretation(
            LocalCommandInterpretationStatus.INVALID,
            invalid_reason=LocalCommandInvalidReason.INVALID_INPUT,
        )
    )


def _membership_decision(success: bool = True) -> MembershipDecision:
    if not success:
        return MembershipDecision(False, error_code=MEMBERSHIP_INACTIVE)
    context = _context()
    return MembershipDecision(
        True,
        ActorWorkspaceMembership(
            context.actor,
            context.workspace,
            MembershipStatus.ACTIVE,
        ),
    )


def test_error_constants_have_exact_approved_values() -> None:
    assert ERROR_CODES == (
        "trusted_context_invalid_input",
        "trusted_context_unknown_binding",
        "trusted_context_unknown_workspace",
        "trusted_context_workspace_not_bound",
        "trusted_context_resolution_failed",
    )
    public_error_values = {
        value
        for name, value in vars(trusted_models).items()
        if name.startswith("TRUSTED_CONTEXT_") and isinstance(value, str)
    }
    assert public_error_values == set(ERROR_CODES)


def test_host_input_preserves_valid_and_invalid_boundary_values() -> None:
    valid = TrustedHostRequestInput("binding", "workspace")
    opaque = object()
    invalid = TrustedHostRequestInput(opaque, " ")
    assert (valid.binding_key, valid.requested_workspace_id) == (
        "binding",
        "workspace",
    )
    assert invalid.binding_key is opaque
    assert invalid.requested_workspace_id == " "


def test_host_input_is_frozen_slotted_and_has_only_boundary_fields() -> None:
    request = TrustedHostRequestInput("binding", "workspace")
    assert tuple(field.name for field in fields(request)) == (
        "binding_key",
        "requested_workspace_id",
    )
    assert not hasattr(request, "__dict__")
    for forbidden in ("actor", "permission", "token", "credential"):
        assert not hasattr(request, forbidden)
    with pytest.raises(FrozenInstanceError):
        request.binding_key = "other"
    with pytest.raises((FrozenInstanceError, TypeError)):
        request.actor = object()


def test_trusted_context_requires_exact_identity_types_and_is_frozen() -> None:
    context = _context()
    assert type(context.actor) is ActorIdentity
    assert type(context.workspace) is WorkspaceIdentity
    with pytest.raises(ValueError):
        TrustedRequestContext(object(), context.workspace)
    with pytest.raises(ValueError):
        TrustedRequestContext(context.actor, object())
    with pytest.raises(FrozenInstanceError):
        context.actor = ActorIdentity("other")


def test_trusted_context_contains_no_extra_trust_or_auth_metadata() -> None:
    context = _context()
    assert tuple(field.name for field in fields(context)) == ("actor", "workspace")
    for forbidden in (
        "permissions",
        "binding_key",
        "authentication_claim",
        "timestamp",
        "session",
        "transport",
    ):
        assert not hasattr(context, forbidden)


def test_resolution_accepts_success_and_each_approved_failure() -> None:
    context = _context()
    success = TrustedRequestContextResolution(True, context)
    assert success.context is context
    assert success.error_code is None
    for error_code in ERROR_CODES:
        failure = TrustedRequestContextResolution(False, error_code=error_code)
        assert failure.context is None
        assert failure.error_code == error_code


@pytest.mark.parametrize(
    "args",
    (
        (True,),
        (True, _context(), TRUSTED_CONTEXT_INVALID_INPUT),
        (False, _context(), TRUSTED_CONTEXT_INVALID_INPUT),
        (False,),
        (False, None, "unsupported"),
        (1, _context(), None),
    ),
)
def test_resolution_rejects_inconsistent_or_unsupported_values(args) -> None:
    with pytest.raises(ValueError):
        TrustedRequestContextResolution(*args)


def test_resolution_is_frozen() -> None:
    resolution = _successful_resolution()
    with pytest.raises(FrozenInstanceError):
        resolution.success = False


def test_configured_binding_normalizes_values_and_preserves_case() -> None:
    actor = ActorIdentity("actor")
    binding = ConfiguredTrustedHostBinding(
        " Key ",
        actor,
        frozenset((" Home ", "Home", "Other")),
    )
    assert binding.binding_key == "Key"
    assert binding.actor is actor
    assert binding.workspace_ids == frozenset(("Home", "Other"))
    assert type(binding.workspace_ids) is frozenset


@pytest.mark.parametrize("binding_key", ("", " ", 1, None))
def test_configured_binding_rejects_invalid_key(binding_key) -> None:
    with pytest.raises(ValueError):
        ConfiguredTrustedHostBinding(
            binding_key,
            ActorIdentity("actor"),
            frozenset(("workspace",)),
        )


def test_configured_binding_requires_exact_actor_and_actual_frozenset() -> None:
    with pytest.raises(ValueError):
        ConfiguredTrustedHostBinding("key", object(), frozenset(("workspace",)))
    for workspace_ids in (set(("workspace",)), tuple(("workspace",)), frozenset()):
        with pytest.raises(ValueError):
            ConfiguredTrustedHostBinding(
                "key",
                ActorIdentity("actor"),
                workspace_ids,
            )


@pytest.mark.parametrize(
    "workspace_ids",
    (frozenset(("",)), frozenset((" ",)), frozenset((1,))),
)
def test_configured_binding_rejects_invalid_workspace_ids(workspace_ids) -> None:
    with pytest.raises(ValueError):
        ConfiguredTrustedHostBinding(
            "key",
            ActorIdentity("actor"),
            workspace_ids,
        )


def test_configured_binding_is_frozen_and_has_no_mutation_api() -> None:
    binding = ConfiguredTrustedHostBinding(
        "key",
        ActorIdentity("actor"),
        frozenset(("workspace",)),
    )
    with pytest.raises(FrozenInstanceError):
        binding.binding_key = "other"
    assert not hasattr(binding, "add_workspace")
    assert not hasattr(binding, "remove_workspace")


def test_local_command_request_preserves_text_and_is_frozen() -> None:
    host_input = TrustedHostRequestInput("key", "workspace")
    authorization = CognitiveFallbackAuthorization(False)
    text = object()
    request = TrustedLocalCommandRequest(host_input, text, authorization)
    assert request.host_input is host_input
    assert request.text is text
    assert request.fallback_authorization is authorization
    with pytest.raises(FrozenInstanceError):
        request.text = "other"


def test_local_command_request_requires_exact_boundary_values() -> None:
    authorization = CognitiveFallbackAuthorization(False)
    with pytest.raises(ValueError):
        TrustedLocalCommandRequest(object(), "text", authorization)
    with pytest.raises(ValueError):
        TrustedLocalCommandRequest(
            TrustedHostRequestInput("key", "workspace"),
            "text",
            object(),
        )


def test_routing_result_accepts_consistent_outcomes_and_preserves_identity() -> None:
    routing_result = _routing_result()
    trust_resolution = _successful_resolution()
    membership_decision = _membership_decision()
    success = TrustedLocalCommandRoutingResult(
        trust_resolution, membership_decision, routing_result
    )
    failure = TrustedLocalCommandRoutingResult(_failed_resolution())
    membership_failure = _membership_decision(False)
    denied = TrustedLocalCommandRoutingResult(
        trust_resolution,
        membership_failure,
    )
    assert success.trust_resolution is trust_resolution
    assert success.membership_decision is membership_decision
    assert success.text_routing_result is routing_result
    assert denied.membership_decision is membership_failure
    assert denied.text_routing_result is None
    assert failure.membership_decision is None
    assert failure.text_routing_result is None


def test_routing_result_rejects_inconsistent_or_invalid_values() -> None:
    trust_success = _successful_resolution()
    trust_failure = _failed_resolution()
    membership_success = _membership_decision()
    membership_failure = _membership_decision(False)
    routing_result = _routing_result()
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(trust_success)
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(trust_failure, membership_success)
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(trust_failure, None, routing_result)
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(
            trust_success,
            membership_failure,
            routing_result,
        )
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(trust_success, membership_success)
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(trust_success, object())
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(
            trust_success,
            membership_success,
            object(),
        )
    with pytest.raises(ValueError):
        TrustedLocalCommandRoutingResult(object())


def test_routing_result_is_frozen_and_does_not_flatten_router_fields() -> None:
    result = TrustedLocalCommandRoutingResult(
        _successful_resolution(), _membership_decision(), _routing_result()
    )
    assert tuple(field.name for field in fields(result)) == (
        "trust_resolution",
        "membership_decision",
        "text_routing_result",
    )
    assert not hasattr(result, "success")
    assert not hasattr(result, "binding_key")
    assert not hasattr(result, "permissions")
    assert not hasattr(result, "interpretation")
    with pytest.raises(FrozenInstanceError):
        result.text_routing_result = None


def test_public_protocol_and_symbols_exclude_future_implementations() -> None:
    assert (
        trusted_context.TrustedRequestContextResolver
        is TrustedRequestContextResolver
    )
    for name in (
        "TRUSTED_CONTEXT_INVALID_INPUT",
        "TRUSTED_CONTEXT_RESOLUTION_FAILED",
        "TRUSTED_CONTEXT_UNKNOWN_BINDING",
        "TRUSTED_CONTEXT_UNKNOWN_WORKSPACE",
        "TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND",
        "ConfiguredTrustedHostBinding",
        "ConfiguredTrustedRequestContextResolver",
        "TrustedHostRequestInput",
        "TrustedLocalCommandRequest",
        "TrustedLocalCommandRoutingResult",
        "TrustedLocalCommandRoutingService",
        "TrustedRequestContext",
        "TrustedRequestContextResolution",
        "TrustedRequestContextResolver",
    ):
        assert name in trusted_context.__all__
        assert hasattr(trusted_context, name)
