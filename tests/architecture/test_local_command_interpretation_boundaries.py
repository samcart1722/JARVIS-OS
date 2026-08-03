"""Architecture checks for the deterministic interpretation boundary."""

import ast
from pathlib import Path


def _imports(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_interpretation_has_no_infrastructure_or_operations_dependencies() -> None:
    forbidden = (
        "sqlite3",
        "app.infrastructure",
        "fastapi",
        "requests",
        "httpx",
        "ollama",
        "settings",
        "operations",
    )
    for path in Path("app/cognition/interpretation").glob("*.py"):
        imports = _imports(str(path))
        assert not any(term in name.lower() for name in imports for term in forbidden)


def test_public_http_does_not_import_interpretation() -> None:
    for path in ("app/api/routes/brain.py", "app/cognition/engine.py"):
        assert not any(
            name.startswith("app.cognition.interpretation")
            for name in _imports(path)
        )


def test_demo_runtime_receives_composition_and_constructs_no_infrastructure() -> None:
    path = "app/operations/local_command_interpretation_demo_runtime.py"
    source = Path(path).read_text(encoding="utf-8")
    imports = _imports(path)
    assert "Container(" not in source
    assert "Settings(" not in source
    assert not any(
        name.startswith(("app.core", "app.infrastructure", "app.models"))
        for name in imports
    )
