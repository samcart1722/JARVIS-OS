"""Deterministic configured trusted request context resolution."""

from types import MappingProxyType

from app.cognition.local_resolution.models import WorkspaceIdentity
from app.cognition.trusted_context.models import (
    TRUSTED_CONTEXT_INVALID_INPUT,
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
    TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
    ConfiguredTrustedHostBinding,
    TrustedHostRequestInput,
    TrustedRequestContext,
    TrustedRequestContextResolution,
)


class ConfiguredTrustedRequestContextResolver:
    __slots__ = ("_bindings_by_key", "_workspaces_by_id")

    def __init__(
        self,
        bindings: tuple[ConfiguredTrustedHostBinding, ...] = (),
        known_workspaces: tuple[WorkspaceIdentity, ...] = (),
    ) -> None:
        if type(known_workspaces) is not tuple:
            raise ValueError("Known workspaces must be a tuple.")

        workspace_lookup: dict[str, WorkspaceIdentity] = {}
        for workspace in known_workspaces:
            if type(workspace) is not WorkspaceIdentity:
                raise ValueError("Known workspace configuration is invalid.")
            if workspace.workspace_id in workspace_lookup:
                raise ValueError("Known workspace IDs must be unique.")
            workspace_lookup[workspace.workspace_id] = workspace
        self._workspaces_by_id = MappingProxyType(workspace_lookup)

        if type(bindings) is not tuple:
            raise ValueError("Configured bindings must be a tuple.")

        binding_lookup: dict[str, ConfiguredTrustedHostBinding] = {}
        for binding in bindings:
            if type(binding) is not ConfiguredTrustedHostBinding:
                raise ValueError("Configured binding is invalid.")
            if binding.binding_key in binding_lookup:
                raise ValueError("Configured binding keys must be unique.")
            for workspace_id in binding.workspace_ids:
                if workspace_id not in workspace_lookup:
                    raise ValueError(
                        "Configured binding references an unknown workspace."
                    )
            binding_lookup[binding.binding_key] = binding
        self._bindings_by_key = MappingProxyType(binding_lookup)

    def resolve(
        self,
        request: TrustedHostRequestInput,
    ) -> TrustedRequestContextResolution:
        if type(request) is not TrustedHostRequestInput:
            raise TypeError("A valid trusted host request is required.")

        if not isinstance(request.binding_key, str) or not request.binding_key.strip():
            return TrustedRequestContextResolution(
                False,
                error_code=TRUSTED_CONTEXT_INVALID_INPUT,
            )
        binding_key = request.binding_key.strip()

        if (
            not isinstance(request.requested_workspace_id, str)
            or not request.requested_workspace_id.strip()
        ):
            return TrustedRequestContextResolution(
                False,
                error_code=TRUSTED_CONTEXT_INVALID_INPUT,
            )
        workspace_id = request.requested_workspace_id.strip()

        binding = self._bindings_by_key.get(binding_key)
        if binding is None:
            return TrustedRequestContextResolution(
                False,
                error_code=TRUSTED_CONTEXT_UNKNOWN_BINDING,
            )

        workspace = self._workspaces_by_id.get(workspace_id)
        if workspace is None:
            return TrustedRequestContextResolution(
                False,
                error_code=TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
            )

        if workspace_id not in binding.workspace_ids:
            return TrustedRequestContextResolution(
                False,
                error_code=TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
            )

        return TrustedRequestContextResolution(
            True,
            TrustedRequestContext(binding.actor, workspace),
        )
