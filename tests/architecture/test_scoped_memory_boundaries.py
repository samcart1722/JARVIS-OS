"""AST enforcement for the isolated scoped-memory foundation."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
MODELS = "app/cognition/memory/scoped/models.py"
CONTRACT = "app/cognition/memory/scoped/contracts.py"
IMPLEMENTATION = "app/cognition/memory/scoped/in_memory_repository.py"
CONTEXT_RETRIEVER = "app/cognition/memory/scoped/context_retriever.py"
EXPLICIT_UPDATE = "app/cognition/memory/scoped/explicit_update.py"
NON_CONSUMERS = (
    "app/api/routes/brain.py",
    "app/cognition/providers/ollama_provider.py",
    "app/cognition/specialists/default_specialist.py",
    "app/cognition/planning/capability_executor.py",
    "app/models/ollama_readiness_probe.py",
)


def imports(relative_path: str) -> set[str]:
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_scoped_models_and_contract_have_no_external_or_legacy_dependencies() -> None:
    forbidden = (
        "app.core",
        "app.memory",
        "app.context",
        "fastapi",
        "requests",
        "os",
    )

    for path in (MODELS, CONTRACT):
        assert not {
            module
            for module in imports(path)
            if module.startswith(forbidden)
        }


def test_implementation_does_not_import_legacy_or_global_repository() -> None:
    imported = imports(IMPLEMENTATION)

    assert "app.core.compatibility.legacy_memory_adapter" not in imported
    assert (
        "app.cognition.memory.persistence.in_memory_repository"
        not in imported
    )


def test_context_retriever_depends_on_contract_not_concrete_repository() -> None:
    imported = imports(CONTEXT_RETRIEVER)

    assert "app.cognition.memory.scoped.contracts" in imported
    assert (
        "app.cognition.memory.scoped.in_memory_repository"
        not in imported
    )
    assert "app.cognition.engine" not in imported
    assert "app.core.compatibility.legacy_memory_adapter" not in imported


def test_explicit_update_depends_only_on_writer_contract_and_models() -> None:
    imported = imports(EXPLICIT_UPDATE)
    forbidden = (
        "app.core",
        "app.models",
        "app.memory",
        "app.operations",
        "app.cognition.providers",
        "fastapi",
        "requests",
        "os",
    )

    assert "app.cognition.memory.scoped.contracts" in imported
    assert "app.cognition.memory.scoped.models" in imported
    assert not {
        module
        for module in imported
        if module.startswith(forbidden)
    }


def test_engine_uses_contract_without_concrete_or_legacy_memory() -> None:
    imported = imports("app/cognition/engine.py")

    assert "app.cognition.memory.scoped.contracts" in imported
    assert (
        "app.cognition.memory.scoped.in_memory_repository"
        not in imported
    )
    assert "app.core.compatibility.legacy_memory_adapter" not in imported


def test_public_and_unrelated_runtime_boundaries_do_not_import_memory() -> None:
    for path in NON_CONSUMERS:
        assert not any(
            module.startswith("app.cognition.memory.scoped")
            for module in imports(path)
        )


def test_readers_core_and_provider_do_not_import_update_or_writer() -> None:
    paths = (
        "app/cognition/engine.py",
        "app/cognition/prompts/reasoning.py",
        "app/cognition/memory/scoped/context_retriever.py",
        "app/cognition/providers/ollama_provider.py",
        "app/api/routes/brain.py",
        "app/models/ollama_readiness_probe.py",
    )

    for path in paths:
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "ExplicitMemoryUpdateService" not in source
        assert "ScopedMemoryWriter" not in source
