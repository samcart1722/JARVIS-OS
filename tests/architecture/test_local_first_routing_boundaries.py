"""Architecture boundaries for explicit local-first cognitive routing."""

import ast
from pathlib import Path

ROUTING_FILES = (
    "app/cognition/routing/contracts.py",
    "app/cognition/routing/models.py",
    "app/cognition/routing/coordinator.py",
)


def _imports(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_coordinator_has_no_infrastructure_framework_or_provider_imports() -> None:
    forbidden = (
        "sqlite3",
        "app.infrastructure",
        "fastapi",
        "requests",
        "httpx",
        "ollama",
        "operations",
    )
    for path in ROUTING_FILES:
        imports = _imports(path)
        assert not any(term in name.lower() for name in imports for term in forbidden)


def test_public_http_and_engine_do_not_import_coordinator() -> None:
    for path in ("app/api/routes/brain.py", "app/cognition/engine.py"):
        imports = _imports(path)
        assert not any("app.cognition.routing" in name for name in imports)


def test_demo_runtime_does_not_construct_container_or_infrastructure() -> None:
    path = "app/operations/local_first_cognitive_routing_demo_runtime.py"
    imports = _imports(path)
    source = Path(path).read_text(encoding="utf-8")
    forbidden = ("app.core", "app.infrastructure", "app.models", "requests")
    assert not any(name.startswith(forbidden) for name in imports)
    assert "Container(" not in source


def test_demo_cli_is_thin_container_adapter() -> None:
    path = "scripts/demo_local_first_cognitive_routing.py"
    imports = _imports(path)
    source = Path(path).read_text(encoding="utf-8")
    assert "app.core.container" in imports
    assert "app.operations.local_first_cognitive_routing_demo_runtime" in imports
    assert "LocalFirstCognitiveCoordinator(" not in source
    assert "Ollama" not in source


def test_continuation_resolver_routes_explicitly_without_storage_or_authorization():
    path = "app/cognition/local_resolution/resolver.py"
    imports = _imports(path)
    assert "app.cognition.local_resolution.knowledge_browse_after_capability" in imports
    assert not any(
        name.startswith(("app.infrastructure", "app.api", "app.local_command"))
        for name in imports
    )
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"getattr", "hasattr"}
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "is_allowed",
                    "browse_after",
                    "interpret",
                    "raw_decode",
                }


def test_continuation_composition_never_discovers_ports_or_queries_data():
    tree = ast.parse(Path("app/core/container.py").read_text(encoding="utf-8"))
    build = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_build_local_resolution"
    )
    for node in ast.walk(build):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"getattr", "hasattr"}
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"browse_after", "is_allowed"}
