"""Enforce the standalone BROWSE capability; no composed routing claim."""

import ast
import inspect
from pathlib import Path

import pytest

from app.cognition.local_resolution.knowledge_browse_capability import (
    StructuredKnowledgeBrowseCapability,
)

CAPABILITY = Path("app/cognition/local_resolution/knowledge_browse_capability.py")
ALLOWED_IMPORTS = {
    "app.cognition.local_resolution.capability": {"LocalPermissionDenied"},
    "app.cognition.local_resolution.contracts": {
        "KnowledgeBrowseRepository",
        "LocalRepositoryError",
        "PermissionPolicy",
    },
    "app.cognition.local_resolution.models": {
        "KNOWLEDGE_DISCOVERY_LOOKAHEAD",
        "KNOWLEDGE_DISCOVERY_MAX_RESULTS",
        "ActorIdentity",
        "BrowseKnowledgeRecordsQuery",
        "KnowledgeRecordsBrowsed",
        "WorkspaceIdentity",
        "_validate_browse_summaries",
    },
    "app.cognition.local_resolution.permissions": {"KNOWLEDGE_RECORDS_BROWSE"},
}


def _forbidden_imports(source):
    violations = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            violations.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            allowed = (
                ALLOWED_IMPORTS.get(node.module, set()) if not node.level else set()
            )
            violations.extend(
                f"{node.module}.{alias.name}"
                for alias in node.names
                if alias.name not in allowed
            )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"__import__", "eval", "exec", "open", "getattr"}:
                violations.append(node.func.id)
    return violations


def test_browse_capability_depends_only_on_its_local_ports_and_values():
    assert _forbidden_imports(CAPABILITY.read_text(encoding="utf-8")) == []
    assert tuple(inspect.signature(StructuredKnowledgeBrowseCapability).parameters) == (
        "repository",
        "permissions",
    )
    assert tuple(
        inspect.signature(StructuredKnowledgeBrowseCapability.execute).parameters
    ) == (
        "self",
        "actor",
        "workspace",
        "intent",
    )


@pytest.mark.parametrize(
    "source",
    (
        "import sqlite3 as harmless",
        "from app.core.container import Container as harmless",
        "from app.cognition.local_resolution.contracts "
        "import KnowledgeRecordRepository as R",
        "from app.cognition.local_resolution.permissions "
        "import KNOWLEDGE_RECORDS_READ as P",
        "from app.cognition.providers.ollama_provider import OllamaProvider as P",
        "from app.cognition.routing.coordinator "
        "import LocalFirstCognitiveCoordinator as C",
        "from app.api.routes.local_command import router as r",
        "from .contracts import KnowledgeBrowseRepository",
        "__import__('requests')",
    ),
)
def test_boundary_enforcement_detects_forbidden_imports_even_with_aliases(source):
    assert _forbidden_imports(source)


def test_only_permission_lookup_and_browse_are_called_on_injected_ports():
    tree = ast.parse(CAPABILITY.read_text(encoding="utf-8"))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name):
            if owner.value.id == "self":
                calls.append((owner.attr, node.func.attr))
    assert sorted(calls) == [("_permissions", "is_allowed"), ("_repository", "browse")]


def test_capability_does_not_repair_metadata_or_own_resolution_mapping():
    tree = ast.parse(CAPABILITY.read_text(encoding="utf-8"))
    forbidden = {"sorted", "sort", "strip", "casefold", "normalize", "filter"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else getattr(node.func, "attr", "")
            )
            assert name not in forbidden
        if isinstance(node, ast.Name):
            assert node.id not in {
                "KnowledgeBrowseResolutionResult",
                "LocalFirstResolver",
            }


def test_browse_composition_never_discovers_support_or_queries_storage():
    tree = ast.parse(Path("app/core/container.py").read_text(encoding="utf-8"))
    build = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_build_local_resolution"
    )
    for node in ast.walk(build):
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else getattr(node.func, "attr", "")
            )
            assert name not in {
                "hasattr",
                "getattr",
                "browse",
                "store",
                "read",
                "find_by_key",
            }
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"_storage", "_records", "_repository"}


def test_gateway_projection_has_no_query_or_parser_calls():
    tree = ast.parse(Path("app/local_command/gateway.py").read_text(encoding="utf-8"))
    forbidden = {
        "browse",
        "read",
        "store",
        "find_by_key",
        "interpret",
        "loads",
        "raw_decode",
        "sorted",
        "sort",
        "normalize",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else getattr(node.func, "attr", "")
            )
            assert name not in forbidden
