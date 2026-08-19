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


def test_memory_update_runtime_does_not_construct_infrastructure() -> None:
    path = "app/operations/memory_update_demo_runtime.py"
    imported = imports(path)
    source = (ROOT / path).read_text(encoding="utf-8")

    assert "app.core.config" not in imported
    assert "app.core.container" not in imported
    assert "app.cognition.memory.scoped.in_memory_repository" not in imported
    assert "app.models.ollama_client" not in imported
    assert "app.cognition.providers.ollama_provider" not in imported
    assert "Container(" not in source
    assert "Ollama" not in source


def test_memory_update_cli_is_a_thin_container_adapter() -> None:
    imported = imports("scripts/demo_memory_update.py")

    assert "app.core.config" in imported
    assert "app.core.container" in imported
    assert "app.operations.memory_update_demo_runtime" in imported
    assert not any(
        module.startswith(
            (
                "app.cognition.capabilities",
                "app.cognition.providers",
                "app.cognition.specialists",
                "app.models",
            )
        )
        for module in imported
    )


def test_sprint_15_demo_does_not_acquire_memory_update() -> None:
    source = (ROOT / "scripts/demo_reasoning.py").read_text(encoding="utf-8")

    assert "MEMORY_UPDATE_ENABLED" not in source
    assert "ExplicitMemoryUpdateService" not in source
    assert "explicit_memory_update_service" not in source


def test_grounded_demo_runtime_does_not_construct_infrastructure() -> None:
    path = "app/operations/grounded_reasoning_demo_runtime.py"
    imported = imports(path)
    source = (ROOT / path).read_text(encoding="utf-8")

    assert "app.core.config" not in imported
    assert "app.core.container" not in imported
    assert "app.models.ollama_client" not in imported
    assert "app.cognition.providers.ollama_provider" not in imported
    assert "app.cognition.grounding.provider" not in imported
    assert "Container(" not in source
    assert "Ollama" not in source


def test_grounded_cli_is_a_thin_container_adapter() -> None:
    imported = imports("scripts/demo_grounded_reasoning.py")

    assert "app.core.config" in imported
    assert "app.core.container" in imported
    assert "app.operations.grounded_reasoning_demo_runtime" in imported
    assert not any(
        module.startswith(
            (
                "app.cognition.capabilities",
                "app.cognition.providers",
                "app.cognition.specialists",
                "app.models",
            )
        )
        for module in imported
    )


def test_sprint_15_and_16_demos_do_not_enable_grounding() -> None:
    for path in (
        "scripts/demo_reasoning.py",
        "scripts/demo_memory_update.py",
    ):
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "MEMORY_GROUNDED_RESPONSE_ENABLED" not in source
        assert "EvidenceBoundedReasoningProvider" not in source


def test_durable_demo_is_separate_from_public_runtime() -> None:
    for path in (
        "app/cognition/engine.py",
        "app/api/routes/brain.py",
        "app/main.py",
    ):
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "durable_local_knowledge_demo" not in source


def test_durable_demo_cli_delegates_to_operations_runtime() -> None:
    imported = imports("scripts/demo_durable_local_knowledge.py")
    assert "app.operations.durable_local_knowledge_demo_runtime" in imported
    assert "sqlite3" not in imported
    assert not any(module.startswith("app.cognition") for module in imported)



def test_durable_principal_actor_demo_is_separate_from_public_runtime() -> None:
    demo_name = "durable_principal_actor_mapping_demo"

    for path in (
        "app/cognition/engine.py",
        "app/api/routes/brain.py",
        "app/main.py",
    ):
        source = (ROOT / path).read_text(encoding="utf-8")
        assert demo_name not in source


def test_durable_principal_actor_demo_cli_is_thin() -> None:
    path = "scripts/demo_durable_principal_actor_mapping.py"
    imported = imports(path)

    assert (
        "app.operations.durable_principal_actor_mapping_demo_runtime"
        in imported
    )
    assert "sqlite3" not in imported
    assert "app.core.container" not in imported
    assert "app.infrastructure.local_storage" not in imported
    assert not any(
        module.startswith("app.cognition")
        for module in imported
    )
