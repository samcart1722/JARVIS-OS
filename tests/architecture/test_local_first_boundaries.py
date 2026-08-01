import ast
from pathlib import Path

PURE = (
    "app/cognition/local_resolution/models.py",
    "app/cognition/local_resolution/contracts.py",
    "app/cognition/local_resolution/knowledge_capability.py",
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


def test_cognition_does_not_import_sqlite_or_local_storage() -> None:
    for path in (
        "app/cognition/local_resolution/models.py",
        "app/cognition/local_resolution/contracts.py",
        "app/cognition/local_resolution/repository.py",
        "app/cognition/local_resolution/capability.py",
        "app/cognition/local_resolution/knowledge_capability.py",
        "app/cognition/local_resolution/resolver.py",
    ):
        imported = _imports(path)
        assert "sqlite3" not in imported
        assert not any("infrastructure.local_storage" in name for name in imported)


def test_sqlite_adapter_has_no_framework_provider_or_product_imports() -> None:
    path = "app/infrastructure/local_storage/sqlite_storage.py"
    imported = _imports(path)
    forbidden = ("fastapi", "requests", "ollama", "healthbridge", "family")
    assert not any(term in name.lower() for name in imported for term in forbidden)


def test_public_api_and_engine_do_not_expose_local_knowledge() -> None:
    for path in ("app/cognition/engine.py", "app/api/routes/brain.py"):
        source = Path(path).read_text(encoding="utf-8")
        assert "ReadKnowledgeRecordQuery" not in source
        assert "StoreKnowledgeRecordCommand" not in source
        assert "local_first_resolver" not in source
