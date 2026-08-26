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
REVOCATION_DEMO = (
    APP
    / "operations"
    / "durable_action_permission_revocation_demo_runtime.py"
)
REVOCATION_CLI = (
    ROOT
    / "scripts"
    / "demo_durable_action_permission_revocation.py"
)


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


def test_permission_repository_contracts_are_separate_and_exact() -> None:
    grants = _class(CONTRACTS, "PermissionGrantRepository")
    revocations = _class(
        CONTRACTS,
        "PermissionGrantRevocationRepository",
    )
    policy = _class(CONTRACTS, "PermissionPolicy")

    assert _methods(grants) == {"is_granted", "create"}
    assert _methods(revocations) == {"revoke"}
    assert _methods(policy) == {"is_allowed"}


def test_repository_permission_policy_does_not_own_revocation() -> None:
    policy = _class(PERMISSIONS, "RepositoryPermissionPolicy")
    attributes = {
        node.attr
        for node in ast.walk(policy)
        if isinstance(node, ast.Attribute)
    }
    names = {
        node.id
        for node in ast.walk(policy)
        if isinstance(node, ast.Name)
    }

    assert "revoke" not in _methods(policy)
    assert "revoke" not in attributes
    assert "revoke_permission_grant" not in attributes
    assert "PermissionGrantRevocationRepository" not in names
    assert "PermissionGrantRevocationRepository" not in attributes
    assert not any(
        imported.endswith(".PermissionGrantRevocationRepository")
        for imported in _imports(PERMISSIONS)
    )


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
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef):
                methods = _methods(node)
                if {"is_granted", "create", "revoke"} <= methods:
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
    assert _methods(adapter) == {
        "__init__",
        "is_granted",
        "create",
        "revoke",
    }


def test_api_and_local_command_do_not_own_permission_revocation() -> None:
    prohibited_names = {
        "PermissionGrantRevocationRepository",
        "SQLitePermissionGrantRepository",
        "revoke_permission_grant",
    }

    for root in (APP / "api", APP / "local_command"):
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
            attributes = {
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
            }

            assert not (names & prohibited_names), (
                path,
                sorted(names & prohibited_names),
            )
            assert not (
                attributes
                & {"revoke", "revoke_permission_grant"}
            ), path


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
    tree = _tree(CONTAINER)
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
    attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
    }

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
    assert "PermissionGrantRevocationRepository" not in names
    assert "SQLitePermissionGrantRepository" not in names
    assert "revoke_permission_grant" not in names
    assert not any(
        "revok" in identifier.lower()
        or "revoc" in identifier.lower()
        for identifier in names | attributes
    )


def test_membership_and_principal_auth_do_not_own_permission_persistence() -> None:
    prohibited = {
        "PermissionGrantRepository",
        "PermissionGrantRevocationRepository",
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


def test_revocation_demo_is_operational_only_and_owns_proof() -> None:
    imports = _imports(REVOCATION_DEMO)
    forbidden = (
        "app.api",
        "app.local_command",
        "app.core.container",
        "app.principal_authentication",
        "app.membership",
        "app.cognition.routing",
        "app.cognition.interpretation",
        "app.cognition.engine",
        "app.cognition.providers",
        "app.cognition.grounding",
        "app.models",
        "app.context.providers",
        "fastapi",
        "requests",
        "socket",
        "random",
        "time",
        "datetime",
    )

    assert not any(
        module == prefix
        or module.startswith(f"{prefix}.")
        for module in imports
        for prefix in forbidden
    )
    assert {
        "app.cognition.local_resolution.models.ActorIdentity",
        "app.cognition.local_resolution.models.WorkspaceIdentity",
        (
            "app.cognition.local_resolution.permissions."
            "RepositoryPermissionPolicy"
        ),
        "app.infrastructure.local_storage.SQLiteLocalStorage",
        (
            "app.infrastructure.local_storage."
            "SQLitePermissionGrantRepository"
        ),
    } <= imports

    tree = _tree(REVOCATION_DEMO)
    fixed_identities = {
        target.id: (
            node.value.func.id,
            node.value.args[0].value,
        )
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and (target := node.targets[0])
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Constant)
        and isinstance(node.value.args[0].value, str)
    }
    assert fixed_identities["ACTOR"] == (
        "ActorIdentity",
        "durable-permission-revocation-actor",
    )
    assert fixed_identities["WORKSPACE"] == (
        "WorkspaceIdentity",
        "durable-permission-revocation-workspace",
    )

    source = REVOCATION_DEMO.read_text(encoding="utf-8")
    assert (
        "Demo database must be outside the repository."
        in source
    )


def test_revocation_demo_is_not_wired_into_public_runtime() -> None:
    paths = [
        APP / "main.py",
        APP / "cognition" / "engine.py",
        *(APP / "api").rglob("*.py"),
        *(APP / "local_command").rglob("*.py"),
    ]
    identifiers = (
        "durable_action_permission_revocation_demo_runtime",
        "demo_durable_action_permission_revocation",
    )

    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert not any(
            identifier in source
            for identifier in identifiers
        ), path


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


def test_durable_permission_revocation_cli_is_thin_and_exact() -> None:
    imports = _imports(REVOCATION_CLI)
    assert (
        "app.operations."
        "durable_action_permission_revocation_demo_runtime"
        in imports
    )

    forbidden = (
        "sqlite3",
        "app.infrastructure.local_storage",
        "app.core.container",
        "app.api",
        "app.local_command",
        "app.principal_authentication",
        "app.membership",
        "app.cognition.local_resolution",
        "app.cognition.routing",
        "app.cognition.interpretation",
        "app.cognition.engine",
        "app.cognition.providers",
        "app.cognition.grounding",
        "app.models",
        "app.context.providers",
        "requests",
        "fastapi",
        "socket",
    )
    assert not any(
        module == prefix
        or module.startswith(f"{prefix}.")
        for module in imports
        for prefix in forbidden
    )

    phase_choices = []
    for node in ast.walk(_tree(REVOCATION_CLI)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "phase"
        ):
            choices = next(
                keyword.value
                for keyword in node.keywords
                if keyword.arg == "choices"
            )
            assert isinstance(choices, ast.Tuple)
            phase_choices.append(
                tuple(
                    item.value
                    for item in choices.elts
                    if isinstance(item, ast.Constant)
                )
            )

    assert phase_choices == [("revoke", "verify")]


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
