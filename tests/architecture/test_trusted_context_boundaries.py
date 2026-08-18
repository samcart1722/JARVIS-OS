"""Architecture enforcement for the trusted request-context boundary."""

import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"
TRUSTED_CONTEXT_ROOT = APP_ROOT / "cognition" / "trusted_context"

APPROVED_TEXT_ROUTING_REQUEST_CALLERS = frozenset(
    (
        "app/cognition/trusted_context/routing.py",
        "app/operations/local_command_interpretation_demo_runtime.py",
        "app/operations/local_knowledge_command_demo_runtime.py",
        "app/operations/local_knowledge_discovery_demo_runtime.py",
    )
)

TRUSTED_CONTEXT_FORBIDDEN_IMPORT_PREFIXES = (
    "app.api",
    "app.core",
    "app.infrastructure",
    "app.models",
    "app.operations",
    "app.cognition.providers",
    "fastapi",
    "httpx",
    "jwt",
    "oauth",
    "os",
    "passlib",
    "random",
    "requests",
    "sqlalchemy",
    "sqlite3",
    "time",
)

TRUSTED_CONTEXT_DOWNSTREAM_IMPORT_PREFIXES = (
    "app.cognition.engine",
    "app.cognition.local_resolution.capability",
    "app.cognition.local_resolution.knowledge_capability",
    "app.cognition.local_resolution.permissions",
    "app.cognition.local_resolution.repository",
    "app.cognition.local_resolution.resolver",
    "app.cognition.routing.coordinator",
)

PROHIBITED_DOWNSTREAM_SYMBOLS = frozenset(
    (
        "CognitiveEngine",
        "ExplicitPermissionPolicy",
        "InMemoryKnowledgeRecordRepository",
        "InMemoryListItemRepository",
        "LocalFirstCognitiveCoordinator",
        "LocalFirstResolver",
        "PermissionPolicy",
        "StructuredKnowledgeCapability",
        "StructuredListCapability",
    )
)

TRUSTED_BOUNDARY_SYMBOLS = frozenset(
    (
        "ConfiguredTrustedRequestContextResolver",
        "LocalCommandTextRouter",
        "TextRoutingRequest",
        "TrustedHostRequestInput",
        "TrustedLocalCommandRoutingService",
    )
)

CONCRETE_TRUST_CONFIGURATION_SYMBOLS = frozenset(
    (
        "ConfiguredTrustedHostBinding",
        "ConfiguredTrustedRequestContextResolver",
    )
)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imports_from_tree(tree: ast.AST) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
    return imported


def _imports(path: Path) -> set[str]:
    return _imports_from_tree(_tree(path))


def _relative(path: Path) -> str:
    return path.relative_to(REPOSITORY_ROOT).as_posix()


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
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in constructor_names:
            lines.append(node.lineno)
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "TextRoutingRequest"
        ):
            lines.append(node.lineno)
    return tuple(sorted(lines))


def _referenced_names_from_tree(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
    return names


def _referenced_names(path: Path) -> set[str]:
    return _referenced_names_from_tree(_tree(path))


def _attribute_parts(node: ast.Attribute) -> tuple[str, ...]:
    parts = [node.attr]
    value = node.value
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if not isinstance(value, ast.Name):
        return ()
    parts.append(value.id)
    return tuple(reversed(parts))


def _prohibited_downstream_dependencies(tree: ast.AST) -> set[str]:
    module_matches = {
        name
        for name in _imports_from_tree(tree)
        if name.startswith(TRUSTED_CONTEXT_DOWNSTREAM_IMPORT_PREFIXES)
    }
    symbol_matches: set[str] = set()
    module_aliases: dict[str, str] = {}
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
                if alias.asname:
                    module_aliases[alias.asname] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("app.cognition"):
                symbol_matches.update(
                    f"{node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name in PROHIBITED_DOWNSTREAM_SYMBOLS
                )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        parts = _attribute_parts(node)
        if not parts or parts[-1] not in PROHIBITED_DOWNSTREAM_SYMBOLS:
            continue
        if parts[0] in module_aliases:
            origin_module = ".".join((module_aliases[parts[0]], *parts[1:-1]))
        else:
            origin_module = ".".join(parts[:-1])
            if origin_module not in imported_modules:
                continue
        if origin_module.startswith("app.cognition"):
            symbol_matches.add(f"{origin_module}.{parts[-1]}")
    return module_matches | symbol_matches


def test_direct_text_routing_request_calls_match_approved_whitelist() -> None:
    call_sites = {
        _relative(path): lines
        for path in _python_files(APP_ROOT)
        if (lines := _text_routing_request_calls(path))
    }
    assert frozenset(call_sites) == APPROVED_TEXT_ROUTING_REQUEST_CALLERS, (
        "Direct TextRoutingRequest construction sites differ from the approved "
        f"whitelist: {call_sites}"
    )


def test_trusted_context_has_no_transport_infrastructure_or_runtime_coupling() -> None:
    violations = {}
    forbidden = TRUSTED_CONTEXT_FORBIDDEN_IMPORT_PREFIXES
    for path in _python_files(TRUSTED_CONTEXT_ROOT):
        matches = sorted(
            name for name in _imports(path) if name.startswith(forbidden)
        )
        if matches:
            violations[_relative(path)] = matches
    assert not violations, f"Forbidden trusted-context imports: {violations}"


def test_trusted_context_does_not_own_downstream_authorization_or_routing() -> None:
    violations = {}
    for path in _python_files(TRUSTED_CONTEXT_ROOT):
        matches = sorted(_prohibited_downstream_dependencies(_tree(path)))
        if matches:
            violations[_relative(path)] = matches
    assert not violations, f"Downstream trusted-context imports: {violations}"


def test_downstream_symbol_detection_handles_reexports_aliases_and_attributes() -> None:
    cases = (
        (
            "from app.cognition.routing import LocalFirstCognitiveCoordinator",
            True,
        ),
        (
            "from app.cognition.local_resolution.contracts import PermissionPolicy",
            True,
        ),
        (
            "from app.cognition.routing import "
            "LocalFirstCognitiveCoordinator as Coordinator",
            True,
        ),
        (
            "from app.cognition.local_resolution.contracts import "
            "PermissionPolicy as Policy",
            True,
        ),
        (
            "import app.cognition.routing as routing\n"
            "coordinator = routing.LocalFirstCognitiveCoordinator",
            True,
        ),
        ("from app.cognition.local_resolution import ActorIdentity", False),
        ("PermissionPolicy = 1", False),
        ("class Something:\n    PermissionPolicy = 1", False),
        ("unrelated.LocalFirstCognitiveCoordinator", False),
    )
    for source, expected in cases:
        observed = bool(_prohibited_downstream_dependencies(ast.parse(source)))
        assert observed is expected, source


def test_lower_level_cognition_does_not_depend_on_configured_trust() -> None:
    roots = (
        APP_ROOT / "cognition" / "interpretation",
        APP_ROOT / "cognition" / "local_resolution",
        APP_ROOT / "cognition" / "routing",
    )
    violations = {}
    for root in roots:
        for path in _python_files(root):
            imported_matches = {
                name
                for name in _imports(path)
                if name.startswith("app.cognition.trusted_context.resolver")
                or any(
                    name.endswith(f".{symbol}")
                    for symbol in CONCRETE_TRUST_CONFIGURATION_SYMBOLS
                )
            }
            referenced_matches = (
                _referenced_names(path) & CONCRETE_TRUST_CONFIGURATION_SYMBOLS
            )
            matches = sorted(imported_matches | referenced_matches)
            if matches:
                violations[_relative(path)] = matches
    assert not violations, f"Lower-level configured-trust imports: {violations}"


def test_public_api_does_not_integrate_trusted_routing_or_low_level_router() -> None:
    violations = {}
    api_root = APP_ROOT / "api"
    for path in _python_files(api_root):
        matches = sorted(_referenced_names(path) & TRUSTED_BOUNDARY_SYMBOLS)
        if matches:
            violations[_relative(path)] = matches
    assert not violations, f"Public API trusted-routing references: {violations}"


def test_cognitive_engine_remains_outside_trusted_host_composition() -> None:
    engine_path = APP_ROOT / "cognition" / "engine.py"
    matches = sorted(_referenced_names(engine_path) & TRUSTED_BOUNDARY_SYMBOLS)
    assert not matches, f"CognitiveEngine trusted-routing references: {matches}"


def test_trusted_routing_requires_membership_before_text_request() -> None:
    path = TRUSTED_CONTEXT_ROOT / "routing.py"
    tree = _tree(path)
    service = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and node.name == "TrustedLocalCommandRoutingService"
    )
    constructor = next(
        node
        for node in service.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    assert [argument.arg for argument in constructor.args.args] == [
        "self", "resolver", "membership_service", "router"
    ]
    assert not constructor.args.defaults
    route = next(
        node
        for node in service.body
        if isinstance(node, ast.FunctionDef) and node.name == "route"
    )
    decision_lines = [
        node.lineno
        for node in ast.walk(route)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "decide"
    ]
    text_request_lines = [
        node.lineno
        for node in ast.walk(route)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "TextRoutingRequest"
    ]
    assert len(decision_lines) == len(text_request_lines) == 1
    assert decision_lines[0] < text_request_lines[0]


def test_trusted_context_has_no_product_domain_imports() -> None:
    product_terms = ("healthbridge", "hospital", "logistics", "medical", "pharmacy")
    violations = {}
    for path in _python_files(TRUSTED_CONTEXT_ROOT):
        matches = sorted(
            name
            for name in _imports(path)
            if any(term in name.lower() for term in product_terms)
        )
        if matches:
            violations[_relative(path)] = matches
    assert not violations, f"Product-specific trusted-context imports: {violations}"
