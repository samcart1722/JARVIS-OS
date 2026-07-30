"""Minimal AST enforcement for confirmed active Cognitive Core boundaries."""

import ast
from pathlib import Path

ROOT = Path(__file__).parents[2]

POLICY_FILES = (
    "app/cognition/specialists/reasoning_selection_policy.py",
    "app/cognition/specialists/deterministic_reasoning_selection_policy.py",
)
DEFAULT_SPECIALIST = "app/cognition/specialists/default_specialist.py"
CAPABILITY_EXECUTOR = "app/cognition/planning/capability_executor.py"
COGNITIVE_ENGINE = "app/cognition/engine.py"
COGNITIVE_OUTCOME = "app/cognition/domain/cognitive_outcome.py"
RESPONSE_STAGE = "app/cognition/pipeline/response_stage.py"
PUBLIC_ROUTE = "app/api/routes/brain.py"
READINESS_CONTRACT = "app/operations/provider_readiness.py"
DOMAIN_FILES = tuple(
    str(path.relative_to(ROOT)).replace("\\", "/")
    for path in sorted((ROOT / "app/cognition/domain").glob("*.py"))
)


def imported_modules(relative_path: str) -> set[str]:
    tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def assert_no_forbidden_imports(
    relative_paths: tuple[str, ...],
    forbidden_prefixes: tuple[str, ...],
) -> None:
    violations = []
    for relative_path in relative_paths:
        for module in sorted(imported_modules(relative_path)):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{relative_path} imports {module}")
    assert not violations, "Forbidden active-runtime imports:\n" + "\n".join(
        violations
    )


def test_selection_policy_has_no_infrastructure_dependencies() -> None:
    assert_no_forbidden_imports(
        POLICY_FILES,
        (
            "app.core",
            "app.models",
            "app.cognition.providers",
            "fastapi",
            "requests",
            "os",
        ),
    )


def test_default_specialist_has_no_infrastructure_dependencies() -> None:
    assert_no_forbidden_imports(
        (DEFAULT_SPECIALIST,),
        (
            "app.core",
            "app.models",
            "app.cognition.providers",
            "fastapi",
            "requests",
            "os",
        ),
    )


def test_capability_executor_has_no_concrete_provider_dependencies() -> None:
    assert_no_forbidden_imports(
        (CAPABILITY_EXECUTOR,),
        (
            "app.core",
            "app.models",
            "app.cognition.providers",
            "fastapi",
            "requests",
        ),
    )


def test_public_route_does_not_import_concrete_runtime_parts() -> None:
    assert_no_forbidden_imports(
        (PUBLIC_ROUTE,),
        (
            "app.models",
            "app.cognition.providers",
            "app.cognition.capabilities",
            "app.cognition.specialists",
        ),
    )


def test_cognitive_domain_has_no_infrastructure_dependencies() -> None:
    assert_no_forbidden_imports(
        DOMAIN_FILES,
        (
            "app.core",
            "app.models",
            "app.cognition.providers",
            "fastapi",
            "requests",
            "os",
        ),
    )


def test_outcome_engine_and_response_stage_do_not_import_fastapi() -> None:
    assert_no_forbidden_imports(
        (COGNITIVE_OUTCOME, COGNITIVE_ENGINE, RESPONSE_STAGE),
        ("fastapi",),
    )


def test_http_status_mapping_is_owned_by_public_route() -> None:
    core_files = (COGNITIVE_OUTCOME, COGNITIVE_ENGINE, RESPONSE_STAGE)
    for relative_path in core_files:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "HTTP_STATUS" not in source

    route_source = (ROOT / PUBLIC_ROUTE).read_text(encoding="utf-8")
    assert "_HTTP_STATUS_BY_ERROR_CODE" in route_source


def test_readiness_contract_is_outside_and_independent_of_cognitive_core() -> None:
    assert_no_forbidden_imports(
        (READINESS_CONTRACT,),
        (
            "app.cognition",
            "app.core",
            "app.models",
            "fastapi",
            "requests",
            "os",
        ),
    )
    engine_source = (ROOT / COGNITIVE_ENGINE).read_text(encoding="utf-8")
    route_source = (ROOT / PUBLIC_ROUTE).read_text(encoding="utf-8")
    assert "readiness" not in engine_source.lower()
    assert "readiness" not in route_source.lower()
