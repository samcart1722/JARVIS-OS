"""Immutable values for deterministic trusted request context resolution."""

from dataclasses import dataclass

from app.cognition.interpretation.routing import TextRoutingResult
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.routing.models import CognitiveFallbackAuthorization

TRUSTED_CONTEXT_INVALID_INPUT = "trusted_context_invalid_input"
TRUSTED_CONTEXT_UNKNOWN_BINDING = "trusted_context_unknown_binding"
TRUSTED_CONTEXT_UNKNOWN_WORKSPACE = "trusted_context_unknown_workspace"
TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND = "trusted_context_workspace_not_bound"
TRUSTED_CONTEXT_RESOLUTION_FAILED = "trusted_context_resolution_failed"

_TRUSTED_CONTEXT_ERROR_CODES = frozenset(
    (
        TRUSTED_CONTEXT_INVALID_INPUT,
        TRUSTED_CONTEXT_UNKNOWN_BINDING,
        TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
        TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
        TRUSTED_CONTEXT_RESOLUTION_FAILED,
    )
)


@dataclass(frozen=True, slots=True)
class TrustedHostRequestInput:
    binding_key: object
    requested_workspace_id: object


@dataclass(frozen=True, slots=True)
class TrustedRequestContext:
    actor: ActorIdentity
    workspace: WorkspaceIdentity

    def __post_init__(self) -> None:
        if type(self.actor) is not ActorIdentity:
            raise ValueError("Trusted request actor is invalid.")
        if type(self.workspace) is not WorkspaceIdentity:
            raise ValueError("Trusted request workspace is invalid.")


@dataclass(frozen=True, slots=True)
class TrustedRequestContextResolution:
    success: bool
    context: TrustedRequestContext | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if type(self.success) is not bool:
            raise ValueError("Trusted context resolution success must be explicit.")
        if self.success:
            if type(self.context) is not TrustedRequestContext:
                raise ValueError(
                    "Successful trusted context resolution requires context."
                )
            if self.error_code is not None:
                raise ValueError(
                    "Successful trusted context resolution forbids an error."
                )
            return
        if self.context is not None:
            raise ValueError("Failed trusted context resolution forbids context.")
        if self.error_code not in _TRUSTED_CONTEXT_ERROR_CODES:
            raise ValueError(
                "Failed trusted context resolution requires a valid error."
            )


@dataclass(frozen=True, slots=True)
class ConfiguredTrustedHostBinding:
    binding_key: str
    actor: ActorIdentity
    workspace_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.binding_key, str) or not self.binding_key.strip():
            raise ValueError("Binding key must be a non-empty string.")
        if type(self.actor) is not ActorIdentity:
            raise ValueError("Configured binding actor is invalid.")
        if type(self.workspace_ids) is not frozenset or not self.workspace_ids:
            raise ValueError("Configured workspaces must be a non-empty frozenset.")
        normalized_workspace_ids: set[str] = set()
        for workspace_id in self.workspace_ids:
            if not isinstance(workspace_id, str) or not workspace_id.strip():
                raise ValueError("Configured workspace ID must be a non-empty string.")
            normalized_workspace_ids.add(workspace_id.strip())
        object.__setattr__(self, "binding_key", self.binding_key.strip())
        object.__setattr__(self, "workspace_ids", frozenset(normalized_workspace_ids))


@dataclass(frozen=True, slots=True)
class TrustedLocalCommandRequest:
    host_input: TrustedHostRequestInput
    text: object
    fallback_authorization: CognitiveFallbackAuthorization

    def __post_init__(self) -> None:
        if type(self.host_input) is not TrustedHostRequestInput:
            raise ValueError("Trusted host input is required.")
        if type(self.fallback_authorization) is not CognitiveFallbackAuthorization:
            raise ValueError("Explicit fallback authorization is required.")


@dataclass(frozen=True, slots=True)
class TrustedLocalCommandRoutingResult:
    trust_resolution: TrustedRequestContextResolution
    text_routing_result: TextRoutingResult | None = None

    def __post_init__(self) -> None:
        if type(self.trust_resolution) is not TrustedRequestContextResolution:
            raise ValueError("A valid trusted context resolution is required.")
        if self.trust_resolution.success:
            if type(self.text_routing_result) is not TextRoutingResult:
                raise ValueError(
                    "Successful trust resolution requires a routing result."
                )
            return
        if self.text_routing_result is not None:
            raise ValueError("Failed trust resolution forbids a routing result.")
