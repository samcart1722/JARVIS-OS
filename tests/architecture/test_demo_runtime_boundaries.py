"""Architecture checks for the deliberately small demo adapter."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]


def imports(relative_path: str) -> set[str]:
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }


def test_demo_service_does_not_construct_infrastructure() -> None:
    source = (ROOT / "app/operations/demo_runtime.py").read_text(
        encoding="utf-8"
    )

    assert "Container(" not in source
    assert "Ollama" not in source
    assert "ReasoningCapability" not in source
    imported = imports("app/operations/demo_runtime.py")
    assert "app.core.config" not in imported
    assert "app.core.container" not in imported
    assert "app.models.ollama_client" not in imported
    assert "app.cognition.providers.ollama_provider" not in imported
    assert "app.cognition.memory.scoped.in_memory_repository" not in imported


def test_cli_is_a_thin_container_adapter() -> None:
    imported = imports("scripts/demo_reasoning.py")

    assert "app.core.container" in imported
    assert "app.operations.demo_runtime" in imported
    assert imported & {"app.cognition.memory.scoped.models"}
    assert not any(
        module.startswith(
            (
                "app.cognition.capabilities",
                "app.cognition.providers",
                "app.models",
            )
        )
        for module in imported
    )
    assert not any(module.startswith("app.models") for module in imported)


def test_core_and_public_runtime_do_not_import_demo() -> None:
    paths = (
        "app/cognition/engine.py",
        "app/cognition/prompts/reasoning.py",
        "app/cognition/memory/scoped/context_retriever.py",
        "app/api/routes/brain.py",
    )

    for path in paths:
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "demo_runtime" not in source
        assert "FunctionalCognitiveDemoRuntime" not in source
