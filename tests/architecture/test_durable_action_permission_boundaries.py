"""Architecture enforcement for durable local action permissions."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app"
LOCAL = APP / "cognition" / "local_resolution"
CONTRACTS = LOCAL / "contracts.py"
PERMISSIONS = LOCAL / "permissions.py"
CONTAINER = APP / "core" / "container.py"
SQLITE = APP / "infrastructure" / "local_storage" / "sqlite_storage.py"
DEMO = APP / "operations" / "durable_action_permission_demo_runtime.py"
CLI = ROOT / "scripts" / "demo_durable_action_permission.py"


def _tree(path: Path) -> ast.Module:
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


def _class(path: Path, name: str) -> ast.ClassDef:
    matches = [
        node
        for node in ast.walk(_tree(path))
        if isinstance(node, ast.ClassDef) and node.name == name
    ]
    assert len(matches) == 1
    return matches[0]


def _methods(node: ast.ClassDef) -> set[str]:
    return {
        item.name
        for item in node.body
        if isinstance(item, ast.FunctionDef)
    }


def test_permission_core_has_no_infrastructure_dependency() -> None:
    forbidden = (
        "app.infrastructure",
        "app.core",
        "app.operations",
        "app.membership",
        "app.principal_authentication",
        "app.api",
        "sqlite3",
        "requests",
        "fastapi",
        "sqlalchemy",
    )
    for path in (CONTRACTS, PERMISSIONS):
        imports = _imports(path)
        assert not any(
            module == prefix or module.startswith(f"{prefix}.")
            for module in imports
            for prefix in forbidden
        )


def test_permission_repository_contract_is_narrow_append_only() -> None:
    repository = _class(CONTRACTS, "PermissionGrantRepository")
    assert _methods(repository) == {"is_granted", "create"}


def test_local_resolution_does_not_import_sqlite_storage() -> None:
    for path in LOCAL.glob("*.py"):
        imports = _imports(path)
        assert "sqlite3" not in imports
        assert not any(
            module.startswith("app.infrastructure")
            for module in imports
        )


def test_sqlite_permission_adapter_is_unique_and_narrow() -> None:
    matches = []
    for path in APP.rglob("*.py"):
        if "sqlite" not in path.as_posix().lower():
            continue
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef):
                methods = _methods(node)
                if {"is_granted", "create"} <= methods:
                    matches.append(
                        (
                            path.relative_to(ROOT).as_posix(),
                            node.name,
                        )
                    )

    assert matches == [
        (
            "app/infrastructure/local_storage/sqlite_storage.py",
            "SQLitePermissionGrantRepository",
        )
    ]

    adapter = _class(SQLITE, "SQLitePermissionGrantRepository")
    assert _methods(adapter) == {"__init__", "is_granted", "create"}


def test_permission_schema_is_exact_and_contains_no_role_or_credential_data() -> None:
    storage = _class(SQLITE, "SQLiteLocalStorage")
    method = next(
        item
        for item in storage.body
        if isinstance(item, ast.FunctionDef)
        and item.name == "_create_action_permission_grant_table"
    )

    sql = next(
        node.value
        for node in ast.walk(method)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("CREATE TABLE action_permission_grants")
    )

    normalized = " ".join(sql.split())

    assert normalized == (
        "CREATE TABLE action_permission_grants "
        "(actor_id TEXT NOT NULL COLLATE BINARY, "
        "workspace_id TEXT NOT NULL COLLATE BINARY, "
        "action TEXT NOT NULL COLLATE BINARY, "
        "PRIMARY KEY (actor_id, workspace_id, action))"
    )

    assert not any(
        term in normalized.lower()
        for term in (
            "role",
            "password",
            "credential",
            "proof",
            "secret",
            "token",
            "session",
            "status",
            "created_at",
            "updated_at",
            "expires",
        )
    )


def test_container_uses_contract_without_infrastructure_import() -> None:
    imports = _imports(CONTAINER)

    assert (
        "app.cognition.local_resolution.contracts.PermissionGrantRepository"
        in imports
    )
    assert (
        "app.cognition.local_resolution.permissions.RepositoryPermissionPolicy"
        in imports
    )
    assert "sqlite3" not in imports
    assert not any(
        module.startswith("app.infrastructure")
        for module in imports
    )


def test_membership_and_principal_auth_do_not_own_permission_persistence() -> None:
    prohibited = {
        "PermissionGrantRepository",
        "PermissionGrantRepositoryError",
        "PermissionGrantConflict",
        "RepositoryPermissionPolicy",
        "SQLitePermissionGrantRepository",
    }

    for root in (
        APP / "membership",
        APP / "principal_authentication",
    ):
        for path in root.rglob("*.py"):
            tree = _tree(path)
            names = {
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name)
            }
            names.update(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            )
            assert not (names & prohibited), (
                path,
                sorted(names & prohibited),
            )


def test_durable_permission_demo_is_separate_from_public_runtime() -> None:
    for relative in (
        "app/cognition/engine.py",
        "app/api/routes/brain.py",
        "app/main.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "durable_action_permission_demo" not in source
        assert "SQLitePermissionGrantRepository" not in source


def test_durable_permission_cli_is_thin() -> None:
    imports = _imports(CLI)

    assert (
        "app.operations.durable_action_permission_demo_runtime"
        in imports
    )

    assert "sqlite3" not in imports
    assert "app.core.container" not in imports
    assert "app.infrastructure.local_storage" not in imports
    assert not any(
        module.startswith("app.cognition")
        for module in imports
    )


def test_durable_permission_runtime_has_no_nondeterministic_or_public_dependency(
) -> None:
    imports = _imports(DEMO)

    forbidden = (
        "random",
        "time",
        "datetime",
        "socket",
        "fastapi",
        "app.api",
    )

    assert not any(
        module == prefix
        or module.startswith(f"{prefix}.")
        for module in imports
        for prefix in forbidden
    )

    source = DEMO.read_text(
        encoding="utf-8"
    )

    assert (
        "Demo database must be outside the repository."
        in source
    )

    patch_targets = {
        node.args[0].value
        for node in ast.walk(
            _tree(DEMO)
        )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "patch"
            and node.args
            and isinstance(
                node.args[0],
                ast.Constant,
            )
            and isinstance(
                node.args[0].value,
                str,
            )
        )
    }

    assert {
        "requests.get",
        "requests.post",
    } <= patch_targets
