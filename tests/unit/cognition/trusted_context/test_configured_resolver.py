"""Contract proofs for configured trusted request context resolution."""

from types import MappingProxyType

import pytest

import app.cognition.trusted_context.resolver as resolver_module
from app.cognition.local_resolution.models import ActorIdentity, WorkspaceIdentity
from app.cognition.trusted_context import (
    TRUSTED_CONTEXT_INVALID_INPUT,
    TRUSTED_CONTEXT_UNKNOWN_BINDING,
    TRUSTED_CONTEXT_UNKNOWN_WORKSPACE,
    TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND,
    ConfiguredTrustedHostBinding,
    ConfiguredTrustedRequestContextResolver,
    TrustedHostRequestInput,
)


def _workspace(workspace_id: str = "home") -> WorkspaceIdentity:
    return WorkspaceIdentity(workspace_id)


def _binding(
    key: str = "host-key",
    actor: ActorIdentity | None = None,
    workspace_ids: frozenset[str] = frozenset(("home",)),
) -> ConfiguredTrustedHostBinding:
    return ConfiguredTrustedHostBinding(
        key,
        actor or ActorIdentity("actor"),
        workspace_ids,
    )


def _resolver(
    bindings: tuple[ConfiguredTrustedHostBinding, ...] | None = None,
    workspaces: tuple[WorkspaceIdentity, ...] | None = None,
) -> ConfiguredTrustedRequestContextResolver:
    return ConfiguredTrustedRequestContextResolver(
        bindings if bindings is not None else (_binding(),),
        workspaces if workspaces is not None else (_workspace(),),
    )


def _error(
    resolver: ConfiguredTrustedRequestContextResolver,
    binding_key: object,
    workspace_id: object,
) -> str | None:
    return resolver.resolve(
        TrustedHostRequestInput(binding_key, workspace_id)
    ).error_code


def test_default_empty_configuration_is_valid_and_inert() -> None:
    resolver = ConfiguredTrustedRequestContextResolver()
    assert _error(resolver, "host-key", "home") == TRUSTED_CONTEXT_UNKNOWN_BINDING
    assert _error(resolver, None, "home") == TRUSTED_CONTEXT_INVALID_INPUT


class _TupleSubclass(tuple):
    pass


@pytest.mark.parametrize(
    "value",
    ([], set(), frozenset(), "", b"", _TupleSubclass()),
)
def test_known_workspaces_requires_an_actual_tuple(value) -> None:
    with pytest.raises(ValueError):
        ConfiguredTrustedRequestContextResolver(known_workspaces=value)


@pytest.mark.parametrize(
    "value",
    ([], set(), frozenset(), "", b"", _TupleSubclass()),
)
def test_bindings_requires_an_actual_tuple(value) -> None:
    with pytest.raises(ValueError):
        ConfiguredTrustedRequestContextResolver(bindings=value)


def test_constructor_rejects_invalid_element_types_in_validation_order() -> None:
    with pytest.raises(ValueError, match="Known workspace"):
        ConfiguredTrustedRequestContextResolver((object(),), (object(),))
    with pytest.raises(ValueError, match="Configured binding"):
        ConfiguredTrustedRequestContextResolver((object(),), (_workspace(),))


def test_one_or_multiple_known_workspaces_are_accepted() -> None:
    home = _workspace()
    work = _workspace("work")
    ConfiguredTrustedRequestContextResolver(known_workspaces=(home,))
    ConfiguredTrustedRequestContextResolver(known_workspaces=(home, work))


def test_duplicate_workspace_ids_are_rejected_but_case_distinct_ids_are_valid() -> None:
    with pytest.raises(ValueError, match="unique"):
        ConfiguredTrustedRequestContextResolver(
            known_workspaces=(_workspace(), _workspace())
        )
    ConfiguredTrustedRequestContextResolver(
        known_workspaces=(_workspace("home"), _workspace("Home"))
    )


def test_valid_binding_and_case_distinct_keys_are_accepted() -> None:
    actor_lower = ActorIdentity("lower")
    actor_upper = ActorIdentity("upper")
    resolver = ConfiguredTrustedRequestContextResolver(
        (_binding("key", actor_lower), _binding("Key", actor_upper)),
        (_workspace(),),
    )
    assert resolver.resolve(TrustedHostRequestInput("key", "home")).context.actor is (
        actor_lower
    )
    assert resolver.resolve(TrustedHostRequestInput("Key", "home")).context.actor is (
        actor_upper
    )


def test_duplicate_binding_keys_and_identical_bindings_are_rejected() -> None:
    first = _binding()
    with pytest.raises(ValueError, match="unique"):
        ConfiguredTrustedRequestContextResolver(
            (first, _binding()),
            (_workspace(),),
        )
    with pytest.raises(ValueError, match="unique"):
        ConfiguredTrustedRequestContextResolver(
            (first, first),
            (_workspace(),),
        )


def test_binding_to_unknown_workspace_is_rejected_during_construction() -> None:
    with pytest.raises(ValueError, match="unknown workspace"):
        ConfiguredTrustedRequestContextResolver(
            (_binding(workspace_ids=frozenset(("missing",))),),
            (_workspace(),),
        )


def test_wrong_request_object_type_raises_type_error() -> None:
    resolver = ConfiguredTrustedRequestContextResolver()
    for request in (None, object(), ("key", "home")):
        with pytest.raises(TypeError):
            resolver.resolve(request)


@pytest.mark.parametrize("invalid", (None, 1, True, object(), "", "   "))
def test_invalid_binding_field_returns_invalid_input(invalid) -> None:
    assert _error(_resolver(), invalid, "home") == TRUSTED_CONTEXT_INVALID_INPUT


@pytest.mark.parametrize("invalid", (None, 1, True, object(), "", "   "))
def test_invalid_workspace_field_returns_invalid_input(invalid) -> None:
    assert _error(_resolver(), "host-key", invalid) == TRUSTED_CONTEXT_INVALID_INPUT


def test_request_whitespace_is_trimmed_for_lookup_without_mutating_request() -> None:
    resolver = _resolver()
    request = TrustedHostRequestInput(" host-key ", " home ")
    result = resolver.resolve(request)
    assert result.success
    assert request.binding_key == " host-key "
    assert request.requested_workspace_id == " home "


def test_request_matching_is_case_sensitive() -> None:
    resolver = _resolver()
    assert _error(resolver, "HOST-KEY", "home") == TRUSTED_CONTEXT_UNKNOWN_BINDING
    assert _error(resolver, "host-key", "Home") == TRUSTED_CONTEXT_UNKNOWN_WORKSPACE


def test_failure_precedence_is_deterministic() -> None:
    home = _workspace()
    work = _workspace("work")
    resolver = _resolver(workspaces=(home, work))
    assert _error(resolver, None, "missing") == TRUSTED_CONTEXT_INVALID_INPUT
    assert _error(resolver, "host-key", None) == TRUSTED_CONTEXT_INVALID_INPUT
    assert _error(resolver, "missing", "missing") == TRUSTED_CONTEXT_UNKNOWN_BINDING
    assert _error(resolver, "host-key", "missing") == (
        TRUSTED_CONTEXT_UNKNOWN_WORKSPACE
    )
    assert _error(resolver, "host-key", "work") == (
        TRUSTED_CONTEXT_WORKSPACE_NOT_BOUND
    )


def test_success_preserves_configured_identities_and_creates_fresh_contexts() -> None:
    actor = ActorIdentity("actor")
    workspace = _workspace()
    resolver = _resolver(bindings=(_binding(actor=actor),), workspaces=(workspace,))
    first = resolver.resolve(TrustedHostRequestInput("host-key", "home"))
    second = resolver.resolve(TrustedHostRequestInput("host-key", "home"))
    assert first.success and second.success
    assert first.error_code is None and second.error_code is None
    assert first.context is not second.context
    assert first.context.actor is actor
    assert first.context.workspace is workspace
    assert second.context.actor is actor
    assert second.context.workspace is workspace


def test_binding_can_resolve_multiple_explicit_workspaces_independently() -> None:
    home = _workspace()
    work = _workspace("work")
    binding = _binding(workspace_ids=frozenset(("home", "work")))
    resolver = _resolver(bindings=(binding,), workspaces=(work, home))
    home_result = resolver.resolve(TrustedHostRequestInput("host-key", "home"))
    work_result = resolver.resolve(TrustedHostRequestInput("host-key", "work"))
    assert home_result.context.workspace is home
    assert work_result.context.workspace is work
    assert _error(resolver, "host-key", "") == TRUSTED_CONTEXT_INVALID_INPUT


def test_private_configuration_is_immutable_and_no_mutation_api_exists() -> None:
    resolver = _resolver()
    assert not hasattr(resolver, "__dict__")
    assert isinstance(resolver._bindings_by_key, MappingProxyType)
    assert isinstance(resolver._workspaces_by_id, MappingProxyType)
    with pytest.raises(TypeError):
        resolver._bindings_by_key["other"] = _binding("other")
    with pytest.raises(TypeError):
        resolver._workspaces_by_id["other"] = _workspace("other")
    for name in (
        "grant",
        "revoke",
        "add_binding",
        "remove_binding",
        "register",
        "repository",
        "database",
        "network",
        "provider",
        "model",
    ):
        assert not hasattr(resolver, name)


def test_base_resolver_has_no_artificial_internal_failure_mechanism() -> None:
    resolver = ConfiguredTrustedRequestContextResolver()
    for name in ("failure_hook", "force_failure", "fail_resolution", "callback"):
        assert not hasattr(resolver, name)
    assert not hasattr(resolver_module, "TRUSTED_CONTEXT_RESOLUTION_FAILED")
