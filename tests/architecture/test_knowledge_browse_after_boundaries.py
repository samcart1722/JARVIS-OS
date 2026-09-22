"""Enforce the standalone continuation capability's inward dependencies."""

import ast
from pathlib import Path


def test_browse_after_capability_has_only_local_contract_dependencies():
    tree = ast.parse(
        Path(
            "app/cognition/local_resolution/knowledge_browse_after_capability.py"
        ).read_text(encoding="utf-8")
    )
    allowed = {
        "app.cognition.local_resolution.capability",
        "app.cognition.local_resolution.contracts",
        "app.cognition.local_resolution.models",
        "app.cognition.local_resolution.permissions",
    }
    port_calls = []
    for node in ast.walk(tree):
        assert not isinstance(node, ast.Import)
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed and node.level == 0
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {
                    "getattr",
                    "hasattr",
                    "open",
                    "eval",
                    "exec",
                    "__import__",
                    "sorted",
                    "filter",
                }
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"sort", "strip", "casefold", "normalize"}
                owner = node.func.value
                if isinstance(owner, ast.Attribute) and isinstance(
                    owner.value, ast.Name
                ):
                    if owner.value.id == "self":
                        port_calls.append((owner.attr, node.func.attr))
    assert sorted(port_calls) == [
        ("_permissions", "is_allowed"),
        ("_repository", "browse_after"),
    ]


def test_in_memory_continuation_does_not_import_storage_or_runtime():
    tree = ast.parse(
        Path("app/cognition/local_resolution/repository.py").read_text(encoding="utf-8")
    )
    for node in ast.walk(tree):
        assert not isinstance(node, ast.Import)
        if isinstance(node, ast.ImportFrom):
            assert node.module in {
                "app.cognition.local_resolution.models",
                "app.cognition.local_resolution.contracts",
            }
