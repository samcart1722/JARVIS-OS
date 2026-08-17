"""Architecture enforcement for actor-workspace membership."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
MEMBERSHIP = APP / "membership"


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imports(path: Path) -> set[str]:
    result = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
            result.update(f"{node.module}.{alias.name}" for alias in node.names)
    return result


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def test_membership_imports_only_stdlib_canonical_identities_and_siblings() -> None:
    allowed_external = {
        "app.cognition.local_resolution.models",
        "app.cognition.local_resolution.models.ActorIdentity",
        "app.cognition.local_resolution.models.WorkspaceIdentity",
    }
    violations = {}
    for path in _python_files(MEMBERSHIP):
        invalid = sorted(
            name
            for name in _imports(path)
            if name.split(".")[0] not in sys.stdlib_module_names
            and not name.startswith("app.membership")
            and name not in allowed_external
        )
        if invalid:
            violations[path.relative_to(ROOT).as_posix()] = invalid
    assert not violations, f"Forbidden membership dependencies: {violations}"


def test_membership_owns_no_permission_auth_transport_or_runtime_symbols() -> None:
    prohibited = {
        "PermissionPolicy", "ExplicitPermissionPolicy", "PermissionGrant",
        "FastAPI", "CognitiveEngine", "SQLiteLocalStorage", "sqlite3",
        "login", "password", "credential", "jwt", "oauth", "session", "rbac",
    }
    violations = {}
    for path in _python_files(MEMBERSHIP):
        tree = _tree(path)
        names = {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        } | {
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        }
        matches = sorted(name for name in names if name in prohibited)
        if matches:
            violations[path.relative_to(ROOT).as_posix()] = matches
    assert not violations, f"Membership owns prohibited semantics: {violations}"


def test_canonical_identity_classes_are_defined_once() -> None:
    definitions = {"ActorIdentity": [], "WorkspaceIdentity": []}
    for path in _python_files(APP):
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef) and node.name in definitions:
                definitions[node.name].append(path.relative_to(ROOT).as_posix())
    expected = ["app/cognition/local_resolution/models.py"]
    assert definitions == {name: expected for name in definitions}, definitions


def test_public_api_and_cognitive_engine_do_not_depend_on_membership() -> None:
    paths = (*_python_files(APP / "api"), APP / "cognition" / "engine.py")
    violations = {
        path.relative_to(ROOT).as_posix(): sorted(
            name for name in _imports(path) if name.startswith("app.membership")
        )
        for path in paths
    }
    assert not any(violations.values()), (
        f"Public/engine membership imports: {violations}"
    )


def test_membership_does_not_depend_on_infrastructure_and_sqlite_is_outward() -> None:
    inward = {
        path.relative_to(ROOT).as_posix(): sorted(
            name for name in _imports(path) if name.startswith("app.infrastructure")
        )
        for path in _python_files(MEMBERSHIP)
    }
    assert not any(inward.values()), f"Membership infrastructure imports: {inward}"
    sqlite_path = APP / "infrastructure" / "local_storage" / "sqlite_storage.py"
    imports = _imports(sqlite_path)
    assert "app.membership.contracts" in imports
    assert "app.membership.models" in imports


def test_sqlite_adapter_has_no_transport_auth_or_provider_dependency() -> None:
    path = APP / "infrastructure" / "local_storage" / "sqlite_storage.py"
    forbidden = ("fastapi", "requests", "httpx", "jwt", "oauth", "ollama", "provider")
    matches = sorted(
        name
        for name in _imports(path)
        if any(term in name.lower() for term in forbidden)
    )
    assert not matches, f"SQLite membership adapter forbidden imports: {matches}"


def test_no_second_sqlite_membership_adapter_exists() -> None:
    implementations = []
    required = {"get", "create", "activate", "deactivate"}
    for path in _python_files(APP):
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef):
                methods = {
                    item.name for item in node.body if isinstance(item, ast.FunctionDef)
                }
                if required <= methods and "sqlite" in path.as_posix().lower():
                    implementations.append(
                        (path.relative_to(ROOT).as_posix(), node.name)
                    )
    assert implementations == [
        ("app/infrastructure/local_storage/sqlite_storage.py", "SQLiteLocalStorage")
    ]
