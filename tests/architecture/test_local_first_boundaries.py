import ast
from pathlib import Path

PURE = (
    "app/cognition/local_resolution/models.py",
    "app/cognition/local_resolution/contracts.py",
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


def test_pure_contracts_have_no_infrastructure_dependencies() -> None:
    forbidden = ("ollama", "requests", "fastapi", "settings", "container", "operations")
    for path in PURE:
        imports = _imports(path)
        assert not any(term in name.lower() for name in imports for term in forbidden)


def test_core_and_api_do_not_import_list_implementation() -> None:
    for path in ("app/cognition/engine.py", "app/api/routes/brain.py"):
        assert not any("local_resolution" in name for name in _imports(path))


def test_generic_local_modules_contain_no_family_business_terms() -> None:
    for path in PURE:
        source = Path(path).read_text(encoding="utf-8").lower()
        assert not any(
            term in source for term in ("family", "wife", "shopping", "baby")
        )


def test_operations_runtime_has_no_framework_or_network_imports() -> None:
    imports = _imports("app/operations/local_first_family_demo_runtime.py")
    forbidden = ("settings", "container", "ollama", "requests", "fastapi")
    assert not any(term in name.lower() for name in imports for term in forbidden)


def test_cli_is_thin_and_uses_no_manual_capability_composition() -> None:
    source = Path("scripts/demo_local_first_family_resolution.py").read_text(
        encoding="utf-8"
    )
    assert "StructuredListCapability(" not in source
    assert "InMemoryListItemRepository(" not in source
    assert "CapabilityRegistry(" not in source
