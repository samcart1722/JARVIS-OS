"""Explicit AST boundaries for evidence-bounded reasoning."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]


def imports(relative_path: str) -> set[str]:
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_grounding_models_parser_and_evidence_have_no_infrastructure() -> None:
    paths = (
        "app/cognition/grounding/models.py",
        "app/cognition/grounding/parser.py",
        "app/cognition/grounding/evidence.py",
    )
    forbidden = (
        "app.core",
        "app.models",
        "app.cognition.providers",
        "app.cognition.memory.scoped.in_memory_repository",
        "app.operations",
        "fastapi",
        "requests",
        "os",
    )

    for path in paths:
        assert not {
            module
            for module in imports(path)
            if module.startswith(forbidden)
        }


def test_grounded_provider_has_only_internal_contract_dependencies() -> None:
    path = "app/cognition/grounding/provider.py"
    imported = imports(path)
    source = (ROOT / path).read_text(encoding="utf-8")
    forbidden = (
        "app.core",
        "app.models",
        "app.memory",
        "app.cognition.memory.scoped",
        "app.operations",
        "fastapi",
        "requests",
        "os",
    )

    assert not {
        module for module in imported if module.startswith(forbidden)
    }
    assert "JsonGroundedResponseParser" not in source
    assert "Ollama" not in source


def test_prompt_and_parser_do_not_import_each_other_concretely() -> None:
    prompt_imports = imports("app/cognition/prompts/reasoning.py")
    parser_imports = imports("app/cognition/grounding/parser.py")

    assert "app.cognition.grounding.parser" not in prompt_imports
    assert "app.cognition.prompts.reasoning" not in parser_imports


def test_core_api_readiness_and_memory_update_do_not_import_grounding() -> None:
    paths = (
        "app/cognition/engine.py",
        "app/api/routes/brain.py",
        "app/models/ollama_readiness_probe.py",
        "app/cognition/memory/scoped/explicit_update.py",
    )

    for path in paths:
        assert not any(
            module.startswith("app.cognition.grounding")
            for module in imports(path)
        )
