"""Explicit AST boundaries for claim-level evidence attribution."""

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


def test_claim_modules_obey_explicit_boundaries() -> None:
    forbidden = ("app.core", "app.models", "fastapi", "requests", "os")
    for path in (
        "app/cognition/grounding/claim_models.py",
        "app/cognition/grounding/claim_parser.py",
        "app/cognition/grounding/claim_formatter.py",
        "app/cognition/grounding/claim_provider.py",
    ):
        assert not {item for item in imports(path) if item.startswith(forbidden)}
    assert "app.cognition.grounding.provider" not in imports(
        "app/cognition/grounding/claim_formatter.py"
    )


def test_engine_api_and_readiness_do_not_import_claim_modules() -> None:
    for path in (
        "app/cognition/engine.py",
        "app/api/routes/brain.py",
        "app/models/ollama_readiness_probe.py",
    ):
        assert not any(
            item.startswith("app.cognition.grounding.claim") for item in imports(path)
        )


def test_claim_demo_runtime_does_not_import_composition_or_ollama() -> None:
    runtime_imports = imports(
        "app/operations/claim_evidence_attribution_demo_runtime.py"
    )
    forbidden = (
        "app.core",
        "app.models.ollama",
        "app.cognition.providers.ollama",
    )
    assert not {item for item in runtime_imports if item.startswith(forbidden)}


def test_claim_cli_does_not_construct_core_runtime_components() -> None:
    path = "scripts/demo_claim_evidence_attribution.py"
    source = (ROOT / path).read_text(encoding="utf-8")
    cli_imports = imports(path)
    forbidden = (
        "app.cognition.capabilities",
        "app.cognition.specialists",
        "app.cognition.capabilities.registry",
    )
    assert not {item for item in cli_imports if item.startswith(forbidden)}
    for name in ("ReasoningCapability(", "DefaultSpecialist(", "CapabilityRegistry("):
        assert name not in source


def test_previous_demo_clis_do_not_enable_claim_attribution() -> None:
    for path in (
        "scripts/demo_reasoning.py",
        "scripts/demo_memory_update.py",
        "scripts/demo_grounded_reasoning.py",
    ):
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "MEMORY_CLAIM_EVIDENCE_ATTRIBUTION_ENABLED" not in source


def test_architecture_enforcement_uses_explicit_paths_not_cache_scanning() -> None:
    tree = ast.parse((ROOT / __file__).read_text(encoding="utf-8"))
    scanned_methods = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"glob", "rglob"}
    }
    assert scanned_methods == set()
