"""Architecture enforcement for local principal authentication."""

import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"
PRINCIPAL_AUTH_ROOT = APP_ROOT / "principal_authentication"
ROUTING_PATH = PRINCIPAL_AUTH_ROOT / "routing.py"
MODELS_PATH = PRINCIPAL_AUTH_ROOT / "models.py"
CONTAINER_PATH = APP_ROOT / "core" / "container.py"
SQLITE_STORAGE_PATH = (
    APP_ROOT
    / "infrastructure"
    / "local_storage"
    / "sqlite_storage.py"
)
TRUSTED_ARCHITECTURE_PATH = (
    REPOSITORY_ROOT / "tests" / "architecture" / "test_trusted_context_boundaries.py"
)

PRINCIPAL_AUTH_FILES = frozenset(
    (
        "__init__.py",
        "configured_authenticator.py",
        "configured_mapper.py",
        "contracts.py",
        "models.py",
        "repository_mapper.py",
        "routing.py",
    )
)
CORE_AUTH_FILES = frozenset(
    (
        "configured_authenticator.py",
        "configured_mapper.py",
        "contracts.py",
        "models.py",
        "repository_mapper.py",
    )
)
CORE_FORBIDDEN_IMPORT_PREFIXES = (
    "app.api",
    "app.core",
    "app.infrastructure",
    "app.membership",
    "app.models",
    "app.operations",
    "app.cognition.engine",
    "app.cognition.providers",
    "app.cognition.routing.coordinator",
    "app.cognition.local_resolution.capability",
    "app.cognition.local_resolution.knowledge_capability",
    "app.cognition.local_resolution.permissions",
    "app.cognition.local_resolution.repository",
    "fastapi",
    "httpx",
    "jwt",
    "oauth",
    "passlib",
    "random",
    "requests",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "time",
)
ROUTING_ALLOWED_IMPORTS = frozenset(
    (
        "app.cognition.interpretation.routing",
        "app.cognition.local_resolution.models",
        "app.cognition.routing.models",
        "app.membership.models",
        "app.membership.service",
        "app.principal_authentication.contracts",
        "app.principal_authentication.models",
        "dataclasses",
        "enum",
    )
)
AUTH_BOUNDARY_SYMBOLS = frozenset(
    (
        "AuthenticatedLocalCommandRequest",
        "AuthenticatedLocalCommandRoutingService",
        "AuthenticatedPrincipal",
        "LocalAuthenticationProof",
        "LocalPrincipalAuthenticator",
        "PrincipalActorMapper",
        "PrincipalActorMappingRepository",
        "PrincipalActorMappingResult",
        "PrincipalAuthenticationResult",
        "PrincipalIdentity",
        "RepositoryPrincipalActorMapper",
    )
)
DOWNSTREAM_FORBIDDEN_SYMBOLS = frozenset(
    (
        "AuthenticatedPrincipal",
        "LocalAuthenticationProof",
        "PrincipalActorMappingResult",
        "PrincipalAuthenticationResult",
        "PrincipalIdentity",
    )
)
PERMISSION_SYMBOLS = frozenset(
    ("ExplicitPermissionPolicy", "PermissionGrant", "PermissionPolicy")
)
COMPOSED_AUTH_TYPES = frozenset(
    (
        "AuthenticatedLocalCommandRoutingService",
        "ConfiguredLocalPrincipalAuthenticator",
        "ConfiguredPrincipalActorMapper",
        "RejectingLocalPrincipalAuthenticator",
        "RepositoryPrincipalActorMapper",
    )
)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def _relative_python_paths(paths: tuple[Path, ...], root: Path) -> frozenset[str]:
    return frozenset(path.relative_to(root).as_posix() for path in paths)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


def _import_origins(tree: ast.AST) -> set[str]:
    origins: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            origins.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            origins.add(node.module)
            origins.update(f"{node.module}.{alias.name}" for alias in node.names)
    return origins


def _import_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _referenced_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
    return names


def _imports_matching(tree: ast.AST, prefixes: tuple[str, ...]) -> set[str]:
    return {
        origin
        for origin in _import_origins(tree)
        if _matches_any_module_prefix(origin, prefixes)
    }


def _module_matches_prefix(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


def _matches_any_module_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(_module_matches_prefix(module, prefix) for prefix in prefixes)


def _class(tree: ast.AST, name: str) -> ast.ClassDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def _method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _field_names(class_node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        node.target.id
        for node in class_node.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _attribute_parts(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return ()
    parts.append(current.id)
    return tuple(reversed(parts))


def _resolved_expression_origin(
    expression: ast.AST, bindings: dict[str, str]
) -> str | None:
    if isinstance(expression, ast.Name):
        return bindings.get(expression.id)
    parts = _attribute_parts(expression)
    if not parts or parts[0] not in bindings:
        return None
    return ".".join((bindings[parts[0]], *parts[1:]))


def _resolved_call_origin(call: ast.Call, bindings: dict[str, str]) -> str | None:
    return _resolved_expression_origin(call.func, bindings)


def _bind_name(bindings: dict[str, str], name: str, origin: str | None) -> None:
    if origin is None:
        bindings.pop(name, None)
    else:
        bindings[name] = origin


def _bind_target(
    bindings: dict[str, str], target: ast.AST, origin: str | None
) -> None:
    if isinstance(target, ast.Name):
        _bind_name(bindings, target.id, origin)
    else:
        for node in ast.walk(target):
            if isinstance(node, ast.Name):
                bindings.pop(node.id, None)


def _constructor_calls_in_expression(
    expression: ast.AST, bindings: dict[str, str]
) -> list[tuple[ast.Call, str]]:
    matches = []
    for node in ast.walk(expression):
        if not isinstance(node, ast.Call):
            continue
        origin = _resolved_call_origin(node, bindings)
        if (
            origin is not None
            and _module_matches_prefix(origin, "app.principal_authentication")
            and origin.rsplit(".", 1)[-1] in COMPOSED_AUTH_TYPES
        ):
            matches.append((node, origin))
    return matches


def _analyze_constructor_statements(
    statements: list[ast.stmt], bindings: dict[str, str]
) -> list[tuple[ast.Call, str]]:
    matches: list[tuple[ast.Call, str]] = []
    for statement in statements:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                local_name = alias.asname or alias.name.split(".", 1)[0]
                bindings[local_name] = alias.name if alias.asname else local_name
            continue
        if isinstance(statement, ast.ImportFrom) and statement.module:
            for alias in statement.names:
                bindings[alias.asname or alias.name] = (
                    f"{statement.module}.{alias.name}"
                )
            continue
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definition_expressions = (
                *statement.decorator_list,
                *statement.args.defaults,
                *(value for value in statement.args.kw_defaults if value is not None),
            )
            for expression in definition_expressions:
                matches.extend(_constructor_calls_in_expression(expression, bindings))
            local_bindings = bindings.copy()
            for argument in (
                *statement.args.posonlyargs,
                *statement.args.args,
                *statement.args.kwonlyargs,
            ):
                local_bindings.pop(argument.arg, None)
            if statement.args.vararg:
                local_bindings.pop(statement.args.vararg.arg, None)
            if statement.args.kwarg:
                local_bindings.pop(statement.args.kwarg.arg, None)
            matches.extend(
                _analyze_constructor_statements(statement.body, local_bindings)
            )
            bindings.pop(statement.name, None)
            continue
        if isinstance(statement, ast.ClassDef):
            for expression in (
                *statement.bases,
                *(keyword.value for keyword in statement.keywords),
                *statement.decorator_list,
            ):
                matches.extend(_constructor_calls_in_expression(expression, bindings))
            matches.extend(
                _analyze_constructor_statements(statement.body, bindings.copy())
            )
            bindings.pop(statement.name, None)
            continue
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value
            if value is not None:
                matches.extend(_constructor_calls_in_expression(value, bindings))
                origin = _resolved_expression_origin(value, bindings)
            else:
                origin = None
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else (statement.target,)
            )
            for target in targets:
                _bind_target(bindings, target, origin)
            continue
        matches.extend(_constructor_calls_in_expression(statement, bindings))
    return matches


def _authentication_constructor_call_origins(
    tree: ast.Module,
) -> tuple[tuple[ast.Call, str], ...]:
    return tuple(_analyze_constructor_statements(tree.body, {}))


def _authentication_constructor_calls(tree: ast.Module) -> tuple[ast.Call, ...]:
    return tuple(
        call for call, _origin in _authentication_constructor_call_origins(tree)
    )


def _definition_expressions(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ast.AST, ...]:
    return (
        *node.decorator_list,
        *node.args.defaults,
        *(value for value in node.args.kw_defaults if value is not None),
    )


def _executable_nodes(node: ast.AST):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for expression in _definition_expressions(node):
            yield from _executable_nodes(expression)
        return
    if isinstance(node, ast.Lambda):
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                yield from _executable_nodes(default)
        return
    if isinstance(node, ast.AnnAssign):
        yield from _executable_nodes(node.target)
        if node.value is not None:
            yield from _executable_nodes(node.value)
        return
    if isinstance(node, ast.ClassDef):
        definition_expressions = (
            *node.bases,
            *(keyword.value for keyword in node.keywords),
            *node.decorator_list,
        )
        for expression in definition_expressions:
            yield from _executable_nodes(expression)
        for statement in node.body:
            yield from _executable_nodes(statement)
        return
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _executable_nodes(child)


def _module_level_calls(tree: ast.Module) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for statement in tree.body
        for node in _executable_nodes(statement)
        if isinstance(node, ast.Call)
    )


def _calls(function: ast.FunctionDef, name: str) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and _call_name(node) == name
    )


def _text_routing_request_calls(path: Path) -> tuple[int, ...]:
    tree = _tree(path)
    constructor_names = {"TextRoutingRequest"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            constructor_names.update(
                alias.asname
                for alias in node.names
                if alias.name == "TextRoutingRequest" and alias.asname
            )
    return tuple(
        sorted(
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id in constructor_names
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "TextRoutingRequest"
            )
        )
    )


def _approved_text_request_callers() -> frozenset[str]:
    tree = _tree(TRUSTED_ARCHITECTURE_PATH)
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "APPROVED_TEXT_ROUTING_REQUEST_CALLERS"
            for target in node.targets
        )
    )
    if not (
        isinstance(assignment.value, ast.Call)
        and isinstance(assignment.value.func, ast.Name)
        and assignment.value.func.id == "frozenset"
        and len(assignment.value.args) == 1
    ):
        raise AssertionError("Trusted routing whitelist has unexpected structure.")
    return frozenset(ast.literal_eval(assignment.value.args[0]))


def test_principal_authentication_source_topology_is_exact() -> None:
    observed = _relative_python_paths(
        _python_files(PRINCIPAL_AUTH_ROOT), PRINCIPAL_AUTH_ROOT
    )
    assert observed == PRINCIPAL_AUTH_FILES
    assert CORE_AUTH_FILES < PRINCIPAL_AUTH_FILES
    assert "routing.py" not in CORE_AUTH_FILES


def test_core_authentication_imports_preserve_dependency_direction() -> None:
    violations = {}
    for name in CORE_AUTH_FILES:
        matches = sorted(
            _imports_matching(
                _tree(PRINCIPAL_AUTH_ROOT / name), CORE_FORBIDDEN_IMPORT_PREFIXES
            )
        )
        if matches:
            violations[name] = matches
    assert not violations, f"Forbidden core-authentication imports: {violations}"


def test_principal_mapping_storage_dependency_is_outward_only() -> None:
    tree = _tree(SQLITE_STORAGE_PATH)

    authentication_modules = {
        module
        for module in _import_modules(tree)
        if _module_matches_prefix(
            module,
            "app.principal_authentication",
        )
    }

    assert authentication_modules == {
        "app.principal_authentication.contracts",
        "app.principal_authentication.models",
    }

    forbidden_symbols = {
        "AuthenticatedLocalCommandRoutingService",
        "AuthenticatedPrincipal",
        "LocalAuthenticationProof",
        "LocalPrincipalAuthenticator",
        "PrincipalActorMapper",
        "PrincipalActorMappingResult",
        "PrincipalAuthenticationResult",
        "RepositoryPrincipalActorMapper",
    }

    assert not (
        _referenced_names(tree)
        & forbidden_symbols
    )


def test_authenticated_routing_imports_are_exactly_scoped() -> None:
    imports = _import_modules(_tree(ROUTING_PATH))
    assert imports == ROUTING_ALLOWED_IMPORTS, (
        f"Authenticated routing imports differ from approved scope: {imports}"
    )


def test_authentication_package_has_no_product_or_external_runtime_imports() -> None:
    forbidden = (
        "app.api",
        "app.infrastructure",
        "app.models",
        "app.operations",
        "app.cognition.providers",
        "fastapi",
        "httpx",
        "jwt",
        "oauth",
        "passlib",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
    )
    product_terms = ("healthbridge", "hospital", "logistics", "medical", "pharmacy")
    violations = {}
    for path in _python_files(PRINCIPAL_AUTH_ROOT):
        origins = _import_origins(_tree(path))
        matches = sorted(
            origin
            for origin in origins
            if _matches_any_module_prefix(origin, forbidden)
            or any(term in origin.lower() for term in product_terms)
        )
        if matches:
            violations[_relative(path)] = matches
    assert not violations, f"External/product authentication imports: {violations}"


def test_public_and_lower_layers_do_not_depend_on_authentication_boundary() -> None:
    roots = (
        APP_ROOT / "api",
        APP_ROOT / "cognition" / "interpretation",
        APP_ROOT / "cognition" / "local_resolution",
        APP_ROOT / "cognition" / "routing",
        APP_ROOT / "membership",
        APP_ROOT / "cognition" / "trusted_context",
    )
    violations = {}
    for root in roots:
        for path in _python_files(root):
            matches = sorted(
                origin
                for origin in _import_origins(_tree(path))
                if _module_matches_prefix(origin, "app.principal_authentication")
            )
            if matches:
                violations[_relative(path)] = matches
    engine_matches = sorted(
        origin
        for origin in _import_origins(_tree(APP_ROOT / "cognition" / "engine.py"))
        if _module_matches_prefix(origin, "app.principal_authentication")
    )
    if engine_matches:
        violations["app/cognition/engine.py"] = engine_matches
    reference_roots = (APP_ROOT / "api",)
    for root in reference_roots:
        for path in _python_files(root):
            matches = sorted(_referenced_names(_tree(path)) & AUTH_BOUNDARY_SYMBOLS)
            if matches:
                violations[_relative(path)] = matches
    engine_references = sorted(
        _referenced_names(_tree(APP_ROOT / "cognition" / "engine.py"))
        & AUTH_BOUNDARY_SYMBOLS
    )
    if engine_references:
        violations["app/cognition/engine.py"] = engine_references
    assert not violations, f"Upward authentication dependencies: {violations}"


def test_authenticated_and_trusted_routes_do_not_cross_delegate() -> None:
    authenticated_origins = _import_origins(_tree(ROUTING_PATH))
    trusted_path = APP_ROOT / "cognition" / "trusted_context" / "routing.py"
    trusted_origins = _import_origins(_tree(trusted_path))
    assert not any(
        _module_matches_prefix(origin, "app.cognition.trusted_context")
        for origin in authenticated_origins
    )
    assert not any(
        _module_matches_prefix(origin, "app.principal_authentication")
        for origin in trusted_origins
    )


def test_identity_and_authentication_definitions_are_unique_and_canonical() -> None:
    expected = {
        "ActorIdentity": "app/cognition/local_resolution/models.py",
        "WorkspaceIdentity": "app/cognition/local_resolution/models.py",
        "PrincipalIdentity": "app/principal_authentication/models.py",
        "LocalAuthenticationProof": "app/principal_authentication/models.py",
        "AuthenticatedLocalCommandRoutingService": (
            "app/principal_authentication/routing.py"
        ),
    }
    observed = {name: [] for name in expected}
    for path in _python_files(APP_ROOT):
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef) and node.name in observed:
                observed[node.name].append(_relative(path))
    assert observed == {name: [path] for name, path in expected.items()}


def test_authenticated_service_constructor_has_exact_dependencies() -> None:
    service = _class(_tree(ROUTING_PATH), "AuthenticatedLocalCommandRoutingService")
    constructor = _method(service, "__init__")
    assert [argument.arg for argument in constructor.args.args] == [
        "self",
        "authenticator",
        "mapper",
        "membership_service",
        "router",
    ]
    assert not constructor.args.defaults


def test_authenticated_route_has_one_structurally_ordered_pipeline() -> None:
    service = _class(_tree(ROUTING_PATH), "AuthenticatedLocalCommandRoutingService")
    route = _method(service, "route")
    stage_names = ("authenticate", "map", "WorkspaceIdentity", "decide")
    stages = {name: _calls(route, name) for name in stage_names}
    stages["TextRoutingRequest"] = _calls(route, "TextRoutingRequest")
    route_calls = tuple(
        call
        for call in _calls(route, "route")
        if isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Attribute)
        and call.func.value.attr == "_router"
    )
    assert all(len(calls) == 1 for calls in stages.values())
    assert len(route_calls) == 1
    ordered = (
        stages["authenticate"][0].lineno,
        stages["map"][0].lineno,
        stages["WorkspaceIdentity"][0].lineno,
        stages["decide"][0].lineno,
        route_calls[0].lineno,
    )
    assert ordered == tuple(sorted(ordered)), f"Invalid authenticated order: {ordered}"
    nested_request_calls = tuple(
        node
        for node in ast.walk(route_calls[0])
        if isinstance(node, ast.Call) and _call_name(node) == "TextRoutingRequest"
    )
    assert nested_request_calls == stages["TextRoutingRequest"]


def test_text_routing_request_provenance_uses_existing_whitelist() -> None:
    approved = _approved_text_request_callers()
    actual = frozenset(
        _relative(path)
        for path in _python_files(APP_ROOT)
        if _text_routing_request_calls(path)
    )
    assert actual == approved
    assert "app/principal_authentication/routing.py" in approved


def test_downstream_contracts_do_not_import_authentication_data() -> None:
    roots = (
        APP_ROOT / "cognition" / "interpretation",
        APP_ROOT / "cognition" / "local_resolution",
        APP_ROOT / "cognition" / "routing",
        APP_ROOT / "membership",
    )
    violations = {}
    for root in roots:
        for path in _python_files(root):
            matches = sorted(
                origin
                for origin in _import_origins(_tree(path))
                if _module_matches_prefix(origin, "app.principal_authentication")
                and origin.rsplit(".", 1)[-1] in DOWNSTREAM_FORBIDDEN_SYMBOLS
            )
            if matches:
                violations[_relative(path)] = matches
    assert not violations, f"Authentication data leaked downstream: {violations}"
    text_request = _class(
        _tree(APP_ROOT / "cognition" / "interpretation" / "routing.py"),
        "TextRoutingRequest",
    )
    assert _field_names(text_request) == (
        "actor",
        "workspace",
        "text",
        "fallback_authorization",
    )


def test_authentication_model_fields_preserve_domain_separation() -> None:
    tree = _tree(MODELS_PATH)
    expected = {
        "PrincipalIdentity": ("principal_id",),
        "LocalAuthenticationProof": ("proof",),
        "AuthenticatedPrincipal": ("principal",),
        "PrincipalAuthenticationResult": ("success", "principal", "error_code"),
        "PrincipalActorMappingResult": ("success", "actor", "error_code"),
    }
    assert {
        name: _field_names(_class(tree, name)) for name in expected
    } == expected


def test_authenticated_request_and_result_fields_are_exact() -> None:
    tree = _tree(ROUTING_PATH)
    request = _class(tree, "AuthenticatedLocalCommandRequest")
    result = _class(tree, "AuthenticatedLocalCommandRoutingResult")
    assert _field_names(request) == (
        "authentication_proof",
        "requested_workspace_id",
        "text",
        "fallback_authorization",
    )
    assert _field_names(result) == (
        "authentication_result",
        "mapping_result",
        "workspace_selection_result",
        "membership_decision",
        "text_routing_result",
    )


def test_container_is_the_only_principal_authentication_composition_root() -> None:
    observed = {name: [] for name in COMPOSED_AUTH_TYPES}
    for path in _python_files(APP_ROOT):
        for _node, origin in _authentication_constructor_call_origins(_tree(path)):
            observed[origin.rsplit(".", 1)[-1]].append(_relative(path))
    assert observed == {
        name: ["app/core/container.py"] for name in COMPOSED_AUTH_TYPES
    }


def test_container_build_order_and_falsey_injection_are_explicit() -> None:
    container = _class(_tree(CONTAINER_PATH), "Container")
    constructor = _method(container, "__init__")
    build_names = (
        "_build_local_command_interpretation",
        "_build_membership",
        "_build_principal_authentication",
        "_build_trusted_request_context",
    )
    lines = tuple(_calls(constructor, name)[0].lineno for name in build_names)
    assert lines == tuple(sorted(lines))
    builder = _method(container, "_build_principal_authentication")
    is_not_none_attributes = {
        node.left.attr
        for node in ast.walk(builder)
        if isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.IsNot)
        and isinstance(node.left, ast.Attribute)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value is None
    }
    assert is_not_none_attributes == {
        "_injected_local_principal_authenticator",
        "_injected_principal_actor_mapper",
        "_injected_principal_actor_mapping_repository",
    }
    builder_imports = {
        origin
        for origin in _import_origins(ast.Module(body=builder.body, type_ignores=[]))
        if _matches_any_module_prefix(origin, ("app.infrastructure", "sqlite3"))
    }
    assert not builder_imports


def test_authentication_modules_have_no_import_time_operational_calls() -> None:
    forbidden_calls = {
        "authenticate",
        "map",
        "open",
        "print",
        "socket",
    }
    violations = {}
    for path in _python_files(PRINCIPAL_AUTH_ROOT):
        tree = _tree(path)
        calls = [
            _call_name(node)
            for node in _module_level_calls(tree)
            if _call_name(node) in forbidden_calls
        ]
        if calls:
            violations[_relative(path)] = calls
    assert not violations, f"Import-time authentication side effects: {violations}"


def test_authentication_has_no_permission_or_logging_surface() -> None:
    violations = {}
    for path in _python_files(PRINCIPAL_AUTH_ROOT):
        tree = _tree(path)
        imported = _import_origins(tree)
        matches = {
            origin
            for origin in imported
            if _matches_any_module_prefix(origin, ("logging", "loguru"))
            or origin.rsplit(".", 1)[-1] in PERMISSION_SYMBOLS
        }
        matches.update(
            name
            for name in PERMISSION_SYMBOLS
            if any(
                isinstance(node, ast.Name) and node.id == name
                for node in ast.walk(tree)
            )
        )
        matches.update(
            "print"
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and _call_name(node) == "print"
        )
        if matches:
            violations[_relative(path)] = sorted(matches)
    assert not violations, f"Authentication authorization/logging surface: {violations}"


def test_proof_and_verifier_are_absent_from_formatted_output() -> None:
    sensitive_names = {"proof", "verifier_value"}
    violations = {}
    for path in _python_files(PRINCIPAL_AUTH_ROOT):
        matches = []
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.JoinedStr):
                continue
            referenced = {
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name) and child.id in sensitive_names
            }
            referenced.update(
                child.attr
                for child in ast.walk(node)
                if isinstance(child, ast.Attribute)
                and child.attr in sensitive_names
            )
            matches.extend(sorted(referenced))
        if matches:
            violations[_relative(path)] = matches
    assert not violations, f"Sensitive authentication formatting: {violations}"


def test_import_provenance_helper_avoids_name_false_positives() -> None:
    cases = (
        (
            "from app.principal_authentication import PrincipalIdentity",
            True,
        ),
        (
            "from app.principal_authentication import PrincipalIdentity as Identity",
            True,
        ),
        ("import app.principal_authentication as authentication", True),
        ("PrincipalIdentity = 1", False),
        ("class Holder:\n    PrincipalIdentity = 1", False),
    )
    for source, expected in cases:
        observed = any(
            _module_matches_prefix(origin, "app.principal_authentication")
            for origin in _import_origins(ast.parse(source))
        )
        assert observed is expected, source


def test_relative_topology_helper_distinguishes_nested_and_extra_paths() -> None:
    root = Path("/principal_authentication")
    approved_paths = tuple(root / name for name in PRINCIPAL_AUTH_FILES)
    assert _relative_python_paths(approved_paths, root) == PRINCIPAL_AUTH_FILES
    additions = (
        root / "experimental.py",
        root / "subdir" / "models.py",
        root / "subdir" / "other.py",
    )
    for addition in additions:
        observed = _relative_python_paths((*approved_paths, addition), root)
        assert observed != PRINCIPAL_AUTH_FILES
        assert addition.relative_to(root).as_posix() in observed


def test_constructor_provenance_handles_import_forms_without_false_positives() -> None:
    detected = (
        "from app.principal_authentication import "
        "AuthenticatedLocalCommandRoutingService\n"
        "AuthenticatedLocalCommandRoutingService(None, None, None, None)",
        "from app.principal_authentication import "
        "AuthenticatedLocalCommandRoutingService as Service\n"
        "Service(None, None, None, None)",
        "import app.principal_authentication\n"
        "app.principal_authentication.AuthenticatedLocalCommandRoutingService("
        "None, None, None, None)",
        "import app.principal_authentication as auth\n"
        "auth.AuthenticatedLocalCommandRoutingService(None, None, None, None)",
        "from app.principal_authentication.routing import "
        "AuthenticatedLocalCommandRoutingService as Service\n"
        "Service(None, None, None, None)",
    )
    ignored = (
        "class AuthenticatedLocalCommandRoutingService:\n"
        "    pass\n"
        "AuthenticatedLocalCommandRoutingService()",
        "Service = object\nService()",
        "import unrelated\n"
        "unrelated.AuthenticatedLocalCommandRoutingService()",
    )
    for source in detected:
        assert len(_authentication_constructor_calls(ast.parse(source))) == 1
    for source in ignored:
        assert not _authentication_constructor_calls(ast.parse(source))


def test_constructor_provenance_tracks_assignments_and_rebindings_in_order() -> None:
    cases = (
        (
            "from app.principal_authentication import "
            "AuthenticatedLocalCommandRoutingService as Constructor\n"
            "Service = Constructor\nService()",
            1,
        ),
        (
            "from app.principal_authentication import "
            "AuthenticatedLocalCommandRoutingService as Constructor\n"
            "Service = Constructor\nService2 = Service\nService2()",
            1,
        ),
        (
            "from app.principal_authentication import "
            "AuthenticatedLocalCommandRoutingService as Constructor\n"
            "Service: object = Constructor\nService()",
            1,
        ),
        (
            "from app.principal_authentication import "
            "AuthenticatedLocalCommandRoutingService\n"
            "AuthenticatedLocalCommandRoutingService = object\n"
            "AuthenticatedLocalCommandRoutingService()",
            0,
        ),
        (
            "from app.principal_authentication import "
            "AuthenticatedLocalCommandRoutingService as Service\n"
            "Service()\nService = object\nService()",
            1,
        ),
        (
            "import app.principal_authentication as auth\n"
            "auth.AuthenticatedLocalCommandRoutingService()\n"
            "auth = unrelated\n"
            "auth.AuthenticatedLocalCommandRoutingService()",
            1,
        ),
    )
    for source, expected_count in cases:
        observed = _authentication_constructor_calls(ast.parse(source))
        assert len(observed) == expected_count


def test_module_level_side_effect_traversal_handles_control_flow() -> None:
    detected = (
        "authenticator.authenticate(proof)",
        "if enabled:\n    authenticator.authenticate(proof)",
        "for item in values:\n    mapper.map(item)",
        "while enabled:\n    authenticator.authenticate(proof)",
        "try:\n    authenticator.authenticate(proof)\nexcept Exception:\n    pass",
        "with context:\n    authenticator.authenticate(proof)",
        "match value:\n    case 1:\n        authenticator.authenticate(proof)",
    )
    ignored = (
        "def run():\n    authenticator.authenticate(proof)",
        "class Service:\n    def run(self):\n        mapper.map(principal)",
        "class Plain:\n    pass\ndef function():\n    pass",
    )
    forbidden = {"authenticate", "map"}
    for source in detected:
        names = {_call_name(call) for call in _module_level_calls(ast.parse(source))}
        assert names & forbidden, source
    for source in ignored:
        names = {_call_name(call) for call in _module_level_calls(ast.parse(source))}
        assert not names & forbidden, source


def test_import_time_definition_expressions_are_semantically_traversed() -> None:
    detected = (
        "def f(value=authenticator.authenticate(proof)):\n    pass",
        "def f(*, value=authenticator.authenticate(proof)):\n    pass",
        "@authenticator.authenticate(proof)\ndef f():\n    pass",
        "async def f(value=authenticator.authenticate(proof)):\n    pass",
        "@authenticator.authenticate(proof)\nasync def f():\n    pass",
        "class Example(authenticator.authenticate(proof)):\n    pass",
        "@authenticator.authenticate(proof)\nclass Example:\n    pass",
        "class Example(Base, metaclass=authenticator.authenticate(proof)):\n    pass",
        "class Example:\n    authenticator.authenticate(proof)",
        "class Example:\n    if enabled:\n        authenticator.authenticate(proof)",
        "handler = lambda value=authenticator.authenticate(proof): value",
    )
    ignored = (
        "def f():\n    authenticator.authenticate(proof)",
        "async def f():\n    authenticator.authenticate(proof)",
        "class Example:\n    def method(self):\n"
        "        authenticator.authenticate(proof)",
        "handler = lambda: authenticator.authenticate(proof)",
    )
    for source in detected:
        names = {_call_name(call) for call in _module_level_calls(ast.parse(source))}
        assert "authenticate" in names, source
    for source in ignored:
        names = {_call_name(call) for call in _module_level_calls(ast.parse(source))}
        assert "authenticate" not in names, source


def test_python_314_annotations_are_deferred_but_eager_values_are_traversed() -> None:
    deferred = (
        "def f(x: authenticator.authenticate(proof)):\n    pass",
        "def f() -> authenticator.authenticate(proof):\n    pass",
        "async def f(x: authenticator.authenticate(proof)):\n    pass",
        "x: authenticator.authenticate(proof)",
        "class Example:\n    x: authenticator.authenticate(proof)",
        "class Example:\n    def method(\n"
        "        self, x: authenticator.authenticate(proof)\n"
        "    ):\n        pass",
        "from __future__ import annotations\n"
        "def f(x: authenticator.authenticate(proof)):\n    pass",
    )
    eager = (
        (
            "def f(x: authenticator.authenticate(proof) = "
            "mapper.map(principal)):\n    pass",
            {"map"},
        ),
        (
            "x: authenticator.authenticate(proof) = mapper.map(principal)",
            {"map"},
        ),
        (
            "class Example:\n"
            "    x: authenticator.authenticate(proof) = mapper.map(principal)",
            {"map"},
        ),
        (
            "class Example:\n"
            "    @authenticator.authenticate(proof)\n"
            "    def method(self):\n        pass",
            {"authenticate"},
        ),
    )
    for source in deferred:
        names = {_call_name(call) for call in _module_level_calls(ast.parse(source))}
        assert "authenticate" not in names, source
    for source, expected in eager:
        names = {_call_name(call) for call in _module_level_calls(ast.parse(source))}
        assert names & expected == expected, source
        assert "authenticate" not in names - expected, source


def test_module_prefix_matching_respects_namespace_boundaries() -> None:
    cases = (
        ("time", "time", True),
        ("time.clock", "time", True),
        ("timekeeper", "time", False),
        ("app.infrastructure", "app.infrastructure", True),
        ("app.infrastructure.local_storage", "app.infrastructure", True),
        ("app.infrastructure_tools", "app.infrastructure", False),
        ("app.api.routes", "app.api", True),
        ("app.apiculture", "app.api", False),
    )
    for module, prefix, expected in cases:
        assert _module_matches_prefix(module, prefix) is expected
    assert not _imports_matching(ast.parse("import timekeeper"), ("time",))
