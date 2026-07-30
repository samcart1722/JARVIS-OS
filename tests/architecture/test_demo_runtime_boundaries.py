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


def test_cli_is_a_thin_container_adapter() -> None:
    imported = imports("scripts/demo_reasoning.py")

    assert "app.core.container" in imported
    assert "app.operations.demo_runtime" in imported
    assert not any(module.startswith("app.cognition") for module in imported)
    assert not any(module.startswith("app.models") for module in imported)
