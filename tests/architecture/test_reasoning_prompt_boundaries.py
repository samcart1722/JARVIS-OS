"""AST enforcement for reasoning prompt policy boundaries."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]
PROMPT_BUILDER = "app/cognition/prompts/reasoning.py"
OLLAMA_PROVIDER = "app/cognition/providers/ollama_provider.py"
NON_CONSUMERS = (
    "app/api/routes/brain.py",
    "app/cognition/engine.py",
    "app/cognition/memory/scoped/context_retriever.py",
    "app/models/ollama_readiness_probe.py",
    "app/cognition/planning/capability_executor.py",
    "app/cognition/specialists/default_specialist.py",
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


def test_prompt_builder_has_no_operational_or_infrastructure_dependencies() -> None:
    forbidden = (
        "app.core",
        "app.models",
        "app.operations",
        "app.cognition.memory.scoped.contracts",
        "app.cognition.memory.scoped.context_retriever",
        "app.cognition.memory.scoped.in_memory_repository",
        "fastapi",
        "requests",
        "os",
    )

    assert not {
        module
        for module in imports(PROMPT_BUILDER)
        if module.startswith(forbidden)
    }


def test_ollama_provider_does_not_retrieve_memory() -> None:
    imported = imports(OLLAMA_PROVIDER)

    assert not any("repository" in module for module in imported)
    assert not any("retriever" in module for module in imported)
    assert "app.core.compatibility.legacy_memory_adapter" not in imported


def test_unrelated_runtime_boundaries_do_not_import_prompt_builder() -> None:
    for path in NON_CONSUMERS:
        assert not any(
            module.startswith("app.cognition.prompts")
            for module in imports(path)
        )
