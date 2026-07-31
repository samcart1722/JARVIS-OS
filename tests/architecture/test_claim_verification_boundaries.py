"""Explicit AST boundaries for Sprint 19 verification."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]


def imports(path: str) -> set[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_pure_verification_modules_have_no_infrastructure() -> None:
    forbidden = ("app.core", "app.models", "fastapi", "requests", "os", "persistence")
    for path in (
        "app/cognition/grounding/verification_contract.py",
        "app/cognition/grounding/verification_models.py",
        "app/cognition/grounding/verification_parser.py",
        "app/cognition/grounding/verification_prompt.py",
    ):
        assert not {module for module in imports(path) if module.startswith(forbidden)}

    adapter_imports = imports("app/cognition/grounding/verification_provider.py")
    assert "app.models.ollama_client" in adapter_imports
    assert "requests" in adapter_imports
    for path in (
        "app/cognition/grounding/verification_contract.py",
        "app/cognition/grounding/verification_models.py",
        "app/cognition/grounding/verification_parser.py",
        "app/cognition/grounding/verification_prompt.py",
        "app/cognition/grounding/claim_provider.py",
    ):
        assert "app.models.ollama_client" not in imports(path)
        assert "requests" not in imports(path)

    claim_provider_imports = imports("app/cognition/grounding/claim_provider.py")
    assert "app.cognition.grounding.verification_provider" not in claim_provider_imports
    contract_imports = imports("app/cognition/grounding/verification_contract.py")
    contract_forbidden = (
        "requests",
        "app.models",
        "app.core",
        "fastapi",
        "app.cognition.memory",
        "persistence",
    )
    assert not {
        module for module in contract_imports if module.startswith(contract_forbidden)
    }


def test_engine_api_and_previous_demos_do_not_enable_verification() -> None:
    for path in ("app/cognition/engine.py", "app/api/routes/brain.py"):
        assert not any(
            module.startswith("app.cognition.grounding.verification")
            for module in imports(path)
        )
    for path in (
        "scripts/demo_reasoning.py",
        "scripts/demo_memory_update.py",
        "scripts/demo_grounded_reasoning.py",
        "scripts/demo_claim_evidence_attribution.py",
    ):
        assert "MEMORY_CLAIM_EVIDENCE_VERIFICATION_ENABLED" not in (
            ROOT / path
        ).read_text(encoding="utf-8")


def test_demo_runtime_is_composition_free_and_enforcement_is_explicit() -> None:
    runtime = imports("app/operations/claim_evidence_verification_demo_runtime.py")
    assert not any(
        module.startswith(("app.core", "app.models.ollama")) for module in runtime
    )
    tree = ast.parse((ROOT / __file__).read_text(encoding="utf-8"))
    assert not {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"glob", "rglob"}
    }
