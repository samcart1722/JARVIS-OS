"""Architecture enforcement for the local-command application gateway."""

import ast
import hashlib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"

LOCAL_COMMAND_ROOT = APP_ROOT / "local_command"
LOCAL_COMMAND_MODELS_PATH = LOCAL_COMMAND_ROOT / "models.py"
LOCAL_COMMAND_GATEWAY_PATH = LOCAL_COMMAND_ROOT / "gateway.py"

HTTP_MODEL_PATH = APP_ROOT / "api" / "models" / "local_command.py"
HTTP_ROUTE_PATH = APP_ROOT / "api" / "routes" / "local_command.py"
CONTAINER_PATH = APP_ROOT / "core" / "container.py"

LOCAL_COMMAND_FILES = frozenset(
    (
        "__init__.py",
        "gateway.py",
        "models.py",
    )
)

LOCAL_COMMAND_FORBIDDEN_IMPORT_PREFIXES = (
    "app.api",
    "app.core",
    "app.infrastructure",
    "app.models",
    "app.operations",
    "app.cognition.engine",
    "app.cognition.providers",
    "fastapi",
    "httpx",
    "requests",
    "socket",
    "sqlalchemy",
    "sqlite3",
)

GATEWAY_FORBIDDEN_DOWNSTREAM_IMPORT_PREFIXES = (
    "app.cognition.interpretation.routing",
    "app.cognition.local_resolution.capability",
    "app.cognition.local_resolution.knowledge_capability",
    "app.cognition.local_resolution.permissions",
    "app.cognition.local_resolution.repository",
    "app.cognition.local_resolution.resolver",
    "app.cognition.routing.coordinator",
    "app.membership.service",
)

API_FORBIDDEN_IMPORT_PREFIXES = (
    "app.principal_authentication",
    "app.membership",
    "app.cognition.interpretation",
    "app.cognition.local_resolution",
    "app.cognition.routing",
    "app.cognition.engine",
    "app.infrastructure",
)

API_FORBIDDEN_SYMBOLS = frozenset(
    (
        "ActorIdentity",
        "AuthenticatedLocalCommandRequest",
        "AuthenticatedLocalCommandRoutingService",
        "AuthenticatedPrincipal",
        "CognitiveEngine",
        "DeterministicLocalCommandInterpreter",
        "ExplicitPermissionPolicy",
        "InMemoryKnowledgeRecordRepository",
        "InMemoryListItemRepository",
        "LocalAuthenticationProof",
        "LocalCommandTextRouter",
        "LocalFirstCognitiveCoordinator",
        "LocalFirstResolver",
        "LocalPrincipalAuthenticator",
        "MembershipDecision",
        "MembershipDecisionService",
        "PermissionGrant",
        "PermissionPolicy",
        "PrincipalActorMapper",
        "PrincipalActorMappingRepository",
        "PrincipalActorMappingResult",
        "PrincipalAuthenticationResult",
        "PrincipalIdentity",
        "RepositoryPermissionPolicy",
        "RepositoryPrincipalActorMapper",
        "SQLiteLocalStorage",
        "WorkspaceIdentity",
    )
)

APPLICATION_MODEL_FORBIDDEN_SYMBOLS = API_FORBIDDEN_SYMBOLS | frozenset(
    (
        "CognitiveOutcome",
        "CoordinatedResult",
        "LocalResolutionResult",
    )
)

EXPECTED_HTTP_STATUSES = {
    "INVALID_REQUEST": 400,
    "ACCESS_DENIED": 403,
    "LOCAL_PERMISSION_DENIED": 403,
    "LOCAL_KNOWLEDGE_NOT_FOUND": 404,
    "LOCAL_KNOWLEDGE_CONFLICT": 409,
    "COGNITIVE_FALLBACK_NOT_AUTHORIZED": 409,
    "LOCAL_VALIDATION_FAILED": 503,
    "COGNITIVE_REQUEST_FAILED": 503,
    "SERVICE_UNAVAILABLE": 503,
    "INTERNAL_ERROR": 500,
}

EXPECTED_INTERNAL_ERROR_CONTENT = {
    "success": False,
    "route": None,
    "response": None,
    "error": {
        "code": "internal_error",
        "message": "The request could not be completed.",
    },
}

FROZEN_UNCHANGED_SHA256 = {
    "app/api/routes/brain.py": (
        "c4e44b3d00f287041eb1df0dd66495c9fd8d8dffeae9c559b7eb448446a81719"
    ),
    "app/api/routes/knowledge.py": (
        "9e6bac3e6409992dfa12860fb2387dee8ef831d34fb6bf31be9fff2331a64cc3"
    ),
    "app/knowledge/api.py": (
        "c1bd53dd2cdf3d95be6b552e0b5a1d41ad9ddc78a84dd264dd02db9b1dc0d09f"
    ),
    "app/main.py": (
        "93beddf0c88d33cde760fe3115d91ab9b8bf66ec18e0dbcb6e1477eebc384560"
    ),
    "app/core/lifespan.py": (
        "ba9d34f4c61cf7d260669166ef0dd762d96e68ae9c03fcdb0e797092d64fedfe"
    ),
}


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def _tree(path: Path) -> ast.Module:
    return ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )


def _class(tree: ast.AST, name: str) -> ast.ClassDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def _method(
    class_node: ast.ClassDef,
    name: str,
) -> ast.FunctionDef:
    return next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _function(
    tree: ast.AST,
    name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


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


def _matches_prefix(
    module: str,
    prefix: str,
) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


def _forbidden_imports(
    tree: ast.AST,
    prefixes: tuple[str, ...],
) -> set[str]:
    return {
        module
        for module in _import_modules(tree)
        if any(
            _matches_prefix(module, prefix)
            for prefix in prefixes
        )
    }


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


def _normalized_sha256(path: Path) -> str:
    normalized = path.read_text(encoding="utf-8")
    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def _assignment(
    tree: ast.Module,
    name: str,
) -> ast.Assign:
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == name
            for target in node.targets
        )
    )


def test_local_command_source_topology_is_exact() -> None:
    observed = frozenset(
        path.relative_to(LOCAL_COMMAND_ROOT).as_posix()
        for path in _python_files(LOCAL_COMMAND_ROOT)
    )

    assert observed == LOCAL_COMMAND_FILES


def test_local_command_has_no_transport_infrastructure_or_provider_coupling() -> None:
    violations = {}

    for path in _python_files(LOCAL_COMMAND_ROOT):
        matches = sorted(
            _forbidden_imports(
                _tree(path),
                LOCAL_COMMAND_FORBIDDEN_IMPORT_PREFIXES,
            )
        )
        if matches:
            violations[
                path.relative_to(REPOSITORY_ROOT).as_posix()
            ] = matches

    assert not violations, (
        f"Forbidden local-command imports: {violations}"
    )


def test_gateway_uses_exactly_one_authenticated_routing_dependency() -> None:
    tree = _tree(LOCAL_COMMAND_GATEWAY_PATH)
    gateway = _class(
        tree,
        "LocalCommandApplicationGateway",
    )
    constructor = _method(gateway, "__init__")

    assert [
        argument.arg
        for argument in constructor.args.args
    ] == [
        "self",
        "routing_service",
    ]
    assert not constructor.args.defaults
    assert not constructor.args.kwonlyargs

    annotation = constructor.args.args[1].annotation

    assert annotation is not None
    assert ast.unparse(annotation) == (
        "AuthenticatedLocalCommandRoutingService"
    )

    execute = _method(gateway, "execute")

    authenticated_route_calls = [
        node
        for node in ast.walk(execute)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "route"
        and _attribute_parts(node.func.value)
        == ("self", "_routing_service")
    ]

    assert len(authenticated_route_calls) == 1

    forbidden_direct_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "authenticate",
            "coordinate",
            "decide",
            "map",
            "process",
            "resolve",
        }
    }

    assert not forbidden_direct_calls


def test_gateway_does_not_import_downstream_authority_implementations() -> None:
    tree = _tree(LOCAL_COMMAND_GATEWAY_PATH)

    matches = sorted(
        _forbidden_imports(
            tree,
            GATEWAY_FORBIDDEN_DOWNSTREAM_IMPORT_PREFIXES,
        )
    )

    assert not matches, (
        f"Gateway bypasses authenticated routing boundary: {matches}"
    )


def test_public_api_uses_only_application_gateway_boundary() -> None:
    violations = {}

    for path in (HTTP_MODEL_PATH, HTTP_ROUTE_PATH):
        tree = _tree(path)

        imported = sorted(
            _forbidden_imports(
                tree,
                API_FORBIDDEN_IMPORT_PREFIXES,
            )
        )
        referenced = sorted(
            _referenced_names(tree)
            & API_FORBIDDEN_SYMBOLS
        )

        if imported or referenced:
            violations[
                path.relative_to(REPOSITORY_ROOT).as_posix()
            ] = {
                "imports": imported,
                "symbols": referenced,
            }

    assert not violations, (
        f"HTTP adapter bypasses application gateway: {violations}"
    )

    route_tree = _tree(HTTP_ROUTE_PATH)

    container_accesses = {
        parts[1]
        for node in ast.walk(route_tree)
        if isinstance(node, ast.Attribute)
        and len(parts := _attribute_parts(node)) >= 2
        and parts[0] == "container"
    }

    assert container_accesses == {
        "local_command_application_gateway"
    }


def test_application_result_contract_contains_no_internal_domain_types() -> None:
    tree = _tree(LOCAL_COMMAND_MODELS_PATH)

    assert not (
        _referenced_names(tree)
        & APPLICATION_MODEL_FORBIDDEN_SYMBOLS
    )

    result = _class(
        tree,
        "LocalCommandApplicationResult",
    )

    fields = {
        node.target.id: ast.unparse(node.annotation)
        for node in result.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
    }

    assert fields == {
        "success": "bool",
        "route": "LocalCommandApplicationRoute | None",
        "response": "str | None",
        "error": "LocalCommandApplicationError | None",
    }


def test_application_request_proof_has_no_generic_repr_or_dataclass_surface() -> None:
    tree = _tree(LOCAL_COMMAND_MODELS_PATH)
    request = _class(
        tree,
        "LocalCommandApplicationRequest",
    )

    decorators = {
        ast.unparse(decorator)
        for decorator in request.decorator_list
    }

    assert "dataclass" not in decorators

    slots_assignment = next(
        node
        for node in request.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "__slots__"
            for target in node.targets
        )
    )

    slots = frozenset(
        ast.literal_eval(slots_assignment.value)
    )

    assert slots == frozenset(
        (
            "_allow_cognitive_fallback",
            "_proof",
            "_requested_workspace_id",
            "_text",
        )
    )
    assert "__dict__" not in slots

    representation = _method(request, "__repr__")
    representation_names = _referenced_names(representation)

    assert "proof" not in representation_names
    assert "_proof" not in representation_names

    pickle_reducer = _method(
        request,
        "__reduce_ex__",
    )

    assert [
        argument.arg
        for argument in pickle_reducer.args.args
    ] == ["self", "protocol"]

    reducer_names = _referenced_names(
        pickle_reducer
    )

    assert "proof" not in reducer_names
    assert "_proof" not in reducer_names

    reducer_raises = [
        node
        for node in ast.walk(pickle_reducer)
        if isinstance(node, ast.Raise)
    ]

    assert len(reducer_raises) == 1

    raised_exception = reducer_raises[0].exc

    assert isinstance(
        raised_exception,
        ast.Call,
    )
    assert isinstance(
        raised_exception.func,
        ast.Name,
    )
    assert raised_exception.func.id == "TypeError"
    assert len(raised_exception.args) == 1

    error_message = raised_exception.args[0]

    assert isinstance(
        error_message,
        ast.Constant,
    )
    assert (
        error_message.value
        == "LocalCommandApplicationRequest "
        "serialization is prohibited."
    )


def test_http_transport_keeps_proof_secret_and_avoids_automatic_body_validation(
) -> None:
    model_tree = _tree(HTTP_MODEL_PATH)
    request_model = _class(
        model_tree,
        "LocalCommandHttpRequest",
    )

    proof_field = next(
        node
        for node in request_model.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "proof"
    )

    assert ast.unparse(proof_field.annotation) == "SecretStr"

    route_tree = _tree(HTTP_ROUTE_PATH)
    endpoint = _function(
        route_tree,
        "execute_local_command",
    )

    assert isinstance(endpoint, ast.AsyncFunctionDef)
    assert [
        argument.arg
        for argument in endpoint.args.args
    ] == ["request"]

    request_annotation = endpoint.args.args[0].annotation

    assert request_annotation is not None
    assert ast.unparse(request_annotation) == "Request"

    secret_unwrap_calls = [
        node
        for node in ast.walk(endpoint)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_secret_value"
    ]

    assert len(secret_unwrap_calls) == 1


def test_http_status_mapping_is_closed_and_local_validation_is_503() -> None:
    tree = _tree(HTTP_ROUTE_PATH)

    status_assignment = _assignment(
        tree,
        "_HTTP_STATUS_BY_ERROR_CODE",
    )

    assert isinstance(status_assignment.value, ast.Dict)

    observed = {}

    for key, value in zip(
        status_assignment.value.keys,
        status_assignment.value.values,
        strict=True,
    ):
        assert isinstance(key, ast.Attribute)
        assert isinstance(key.value, ast.Name)
        assert key.value.id == (
            "LocalCommandApplicationErrorCode"
        )
        assert isinstance(value, ast.Constant)
        assert type(value.value) is int

        observed[key.attr] = value.value

    assert observed == EXPECTED_HTTP_STATUSES
    assert observed["LOCAL_VALIDATION_FAILED"] == 503


def test_http_adapter_owns_fixed_unexpected_exception_sanitization() -> None:
    tree = _tree(HTTP_ROUTE_PATH)

    internal_assignment = _assignment(
        tree,
        "_INTERNAL_ERROR_CONTENT",
    )

    assert ast.literal_eval(
        internal_assignment.value
    ) == EXPECTED_INTERNAL_ERROR_CONTENT

    endpoint = _function(
        tree,
        "execute_local_command",
    )

    generic_handlers = [
        handler
        for node in ast.walk(endpoint)
        if isinstance(node, ast.Try)
        for handler in node.handlers
        if isinstance(handler.type, ast.Name)
        and handler.type.id == "Exception"
    ]

    assert len(generic_handlers) == 2

    for handler in generic_handlers:
        fixed_returns = [
            node
            for node in ast.walk(handler)
            if isinstance(node, ast.Return)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id
            == "_fixed_internal_error_response"
        ]

        assert len(fixed_returns) == 1


def test_container_composes_gateway_only_from_existing_authenticated_route() -> None:
    tree = _tree(CONTAINER_PATH)
    container_class = _class(tree, "Container")

    constructor = _method(
        container_class,
        "__init__",
    )

    build_calls = [
        statement.value.func.attr
        for statement in constructor.body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and isinstance(
            statement.value.func.value,
            ast.Name,
        )
        and statement.value.func.value.id == "self"
        and statement.value.func.attr.startswith(
            "_build_"
        )
    ]

    auth_index = build_calls.index(
        "_build_principal_authentication"
    )

    assert build_calls[auth_index + 1] == (
        "_build_local_command_application_gateway"
    )

    build_gateway = _method(
        container_class,
        "_build_local_command_application_gateway",
    )

    constructor_calls = [
        node
        for node in ast.walk(build_gateway)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "LocalCommandApplicationGateway"
    ]

    assert len(constructor_calls) == 1

    call = constructor_calls[0]

    assert len(call.args) == 1
    assert not call.keywords
    assert _attribute_parts(call.args[0]) == (
        "self",
        "authenticated_local_command_routing_service",
    )

    referenced = _referenced_names(build_gateway)

    assert referenced <= {
        "LocalCommandApplicationGateway",
        "_build_local_command_application_gateway",
        "authenticated_local_command_routing_service",
        "local_command_application_gateway",
        "self",
    }

    container_imports = _import_modules(tree)

    assert not {
        module
        for module in container_imports
        if _matches_prefix(
            module,
            "app.infrastructure",
        )
        or module in {
            "sqlalchemy",
            "sqlite3",
        }
    }

    default_container = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "container"
            for target in node.targets
        )
    )

    assert isinstance(default_container.value, ast.Call)
    assert isinstance(
        default_container.value.func,
        ast.Name,
    )
    assert default_container.value.func.id == "Container"
    assert not default_container.value.args
    assert not default_container.value.keywords


def test_frozen_legacy_http_surfaces_remain_byte_semantically_unchanged() -> None:
    observed = {
        relative: _normalized_sha256(
            REPOSITORY_ROOT / relative
        )
        for relative in FROZEN_UNCHANGED_SHA256
    }

    assert observed == FROZEN_UNCHANGED_SHA256