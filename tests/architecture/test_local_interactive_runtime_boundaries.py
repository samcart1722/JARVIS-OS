"""Architecture enforcement for the bounded local interactive runtime."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ORDINARY_APP_PATHS = ("app/main.py", "app/api/router.py")
INTERACTIVE_API_PATHS = (
    "app/api/interactive.py",
    "app/api/routes/local_command.py",
    "app/api/routes/local_ui.py",
)
DEMO_RUNTIME = "app.operations.local_interactive_demo_runtime"


def _tree(relative_path: str) -> ast.Module:
    path = ROOT / relative_path
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imports(relative_path: str) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(_tree(relative_path)):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _attribute_parts(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    current = node

    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value

    if not isinstance(current, ast.Name):
        return ()

    parts.append(current.id)
    return tuple(reversed(parts))


def _import_origins_from_tree(tree: ast.Module) -> set[str]:
    """Resolve imported provenance independently of local aliases."""

    origins: set[str] = set()
    bindings: dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                origins.add(alias.name)

                if alias.asname:
                    bindings[alias.asname] = alias.name
                else:
                    root_name = alias.name.split(".", 1)[0]
                    bindings[root_name] = root_name

        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                origin = f"{node.module}.{alias.name}"
                origins.add(origin)

                if alias.name != "*":
                    bindings[
                        alias.asname or alias.name
                    ] = origin

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            parts = _attribute_parts(node)

            if parts and parts[0] in bindings:
                origin = bindings[parts[0]]

                if len(parts) > 1:
                    origin = (
                        origin
                        + "."
                        + ".".join(parts[1:])
                    )

                origins.add(origin)

        elif (
            isinstance(node, ast.Name)
            and node.id in bindings
        ):
            origins.add(bindings[node.id])

    return origins


def _import_origins(relative_path: str) -> set[str]:
    return _import_origins_from_tree(
        _tree(relative_path)
    )


def _python_paths(root: str) -> tuple[str, ...]:
    return tuple(
        path.relative_to(ROOT).as_posix()
        for path in sorted((ROOT / root).rglob("*.py"))
    )


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


def test_import_provenance_tracks_aliases_for_architecture_enforcement() -> None:
    """Aliasing must not hide authority or structured-result provenance."""

    synthetic = ast.parse(
        "from app.cognition.local_resolution.models "
        "import ListItemsSnapshot as Snapshot\n"
        "import app.cognition.local_resolution.permissions "
        "as local_permissions\n"
        "snapshot_type = Snapshot\n"
        "policy_type = local_permissions.PermissionPolicy\n"
    )

    origins = _import_origins_from_tree(synthetic)

    assert (
        "app.cognition.local_resolution.models.ListItemsSnapshot"
        in origins
    )
    assert (
        "app.cognition.local_resolution.permissions.PermissionPolicy"
        in origins
    )


def test_ordinary_application_remains_separate_from_interactive_runtime() -> None:
    """The historical app and router must not acquire the optional UI runtime."""

    forbidden = (
        "app.api.interactive",
        "app.api.routes.local_ui",
        "app.operations.local_interactive_runtime",
        DEMO_RUNTIME,
        "scripts",
        "uvicorn",
    )
    violations = {
        path: sorted(
            module
            for module in _imports(path)
            if any(_matches(module, prefix) for prefix in forbidden)
        )
        for path in ORDINARY_APP_PATHS
    }
    violations = {path: imports for path, imports in violations.items() if imports}
    assert not violations, f"Ordinary app acquired interactive concerns: {violations}"


def test_product_modules_do_not_depend_on_operations_demo_or_scripts() -> None:
    """Operations proof facilities must never become product dependencies."""

    violations: dict[str, list[str]] = {}
    for path in _python_paths("app"):
        imports = sorted(
            module
            for module in _imports(path)
            if _matches(module, DEMO_RUNTIME) or _matches(module, "scripts")
        )
        if imports:
            violations[path] = imports
    assert not violations, f"Product-to-demo dependency detected: {violations}"


def test_scripts_depend_inward_without_becoming_import_targets() -> None:
    """Launch and proof scripts are outer adapters, never reusable layers."""

    app_violations = {
        path: sorted(module for module in _imports(path) if _matches(module, "scripts"))
        for path in _python_paths("app")
    }
    app_violations = {
        path: imports for path, imports in app_violations.items() if imports
    }
    assert not app_violations, f"Product module imports a script: {app_violations}"

    launcher_imports = _imports("scripts/launch_local_interactive.py")
    demo_imports = _imports("scripts/demo_local_interactive.py")
    assert DEMO_RUNTIME not in launcher_imports, (
        "The normal launcher must not import the operations proof runtime."
    )
    assert "scripts.launch_local_interactive" not in demo_imports, (
        "The operations proof must not reuse the normal launcher."
    )


def test_uvicorn_is_owned_only_by_normal_interactive_launcher() -> None:
    """Programmatic server ownership belongs to one outermost adapter."""

    candidates = _python_paths("app") + _python_paths("scripts")
    owners = {
        path
        for path in candidates
        if any(_matches(module, "uvicorn") for module in _imports(path))
    }
    assert owners == {"scripts/launch_local_interactive.py"}, (
        f"Unexpected Uvicorn ownership: {sorted(owners)}"
    )


def test_interactive_api_does_not_compose_storage_or_authority() -> None:
    """HTTP/UI adapters delegate; they do not construct persistence or policy."""

    forbidden = (
        "app.infrastructure",
        "app.membership",
        "app.principal_authentication",
        "app.cognition.local_resolution.permissions",
        "app.cognition.local_resolution.repository",
        "sqlite3",
        "sqlalchemy",
    )
    violations = {
        path: sorted(
            module
            for module in _imports(path)
            if any(_matches(module, prefix) for prefix in forbidden)
        )
        for path in INTERACTIVE_API_PATHS
    }
    violations = {path: imports for path, imports in violations.items() if imports}
    assert not violations, f"Interactive API composes storage/authority: {violations}"


def test_ui_route_does_not_own_authorization_symbols() -> None:
    """UI import provenance must remain outside authority/capability layers."""

    forbidden_prefixes = (
        "app.cognition.local_resolution",
        "app.infrastructure.local_storage",
        "app.membership",
        "app.principal_authentication",
    )

    origins = _import_origins(
        "app/api/routes/local_ui.py"
    )

    violations = sorted(
        origin
        for origin in origins
        if any(
            _matches(origin, prefix)
            for prefix in forbidden_prefixes
        )
    )

    assert not violations, (
        "UI route acquired authorization, capability, identity, "
        f"membership, or storage provenance: {violations}"
    )


def test_transport_models_preserve_canonical_text_result_boundary() -> None:
    """Public HTTP models must not import internal structured result types."""

    forbidden_names = {
        "CoordinatedResult",
        "KnowledgeDiscoveryResolutionResult",
        "KnowledgeRead",
        "KnowledgeRecordsFound",
        "KnowledgeResolutionResult",
        "KnowledgeStored",
        "ListItemsAdded",
        "ListItemsSnapshot",
        "LocalResolutionResult",
        "StoredKnowledgeRecord",
        "StoredListItem",
    }

    forbidden_prefixes = (
        "app.cognition.local_resolution",
        "app.cognition.routing",
    )

    origins = _import_origins(
        "app/api/models/local_command.py"
    )

    violations = sorted(
        origin
        for origin in origins
        if (
            any(
                _matches(origin, prefix)
                for prefix in forbidden_prefixes
            )
            and origin.rsplit(".", 1)[-1]
            in forbidden_names
        )
    )

    assert not violations, (
        "HTTP models expose internal structured local results: "
        f"{violations}"
    )
