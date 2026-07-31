"""Explicit AST boundaries for Sprint 20 independent verification."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]


def imports(path: str) -> set[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def test_engine_api_and_pure_verification_do_not_know_independent_client() -> None:
    for path in ("app/cognition/engine.py", "app/api/routes/brain.py"):
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "claim_verifier_ollama_client" not in source
    for path in (
        "app/cognition/grounding/verification_contract.py",
        "app/cognition/grounding/verification_models.py",
        "app/cognition/grounding/verification_parser.py",
        "app/cognition/grounding/verification_prompt.py",
    ):
        assert "app.models.ollama_client" not in imports(path)


def test_runtime_is_composition_free_and_previous_demos_do_not_enable_flag() -> None:
    runtime_imports = imports(
        "app/operations/independent_claim_verifier_demo_runtime.py"
    )
    assert not any(
        item.startswith(("app.core", "app.models.ollama")) for item in runtime_imports
    )
    for path in (
        "scripts/demo_reasoning.py",
        "scripts/demo_memory_update.py",
        "scripts/demo_grounded_reasoning.py",
        "scripts/demo_claim_evidence_attribution.py",
        "scripts/demo_claim_evidence_verification.py",
    ):
        assert "MEMORY_INDEPENDENT_CLAIM_VERIFIER_ENABLED" not in (
            ROOT / path
        ).read_text(encoding="utf-8")


def test_enforcement_uses_explicit_paths_and_no_registry_was_introduced() -> None:
    source = (ROOT / "app/core/container.py").read_text(encoding="utf-8")
    assert "ProviderRegistry" not in source
    tree = ast.parse((ROOT / __file__).read_text(encoding="utf-8"))
    assert not {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"glob", "rglob"}
    }
