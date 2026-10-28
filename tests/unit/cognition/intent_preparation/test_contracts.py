"""The extraction port has no dependency on execution or generic reasoning."""

import ast
import inspect
import sys
from pathlib import Path
from typing import get_type_hints

from app.cognition.intent_preparation.contracts import IntentPreparationProvider


class FakePreparationProvider:
    def prepare(self, text: str) -> str:
        return '{"outcome":"unsupported","intent":null,"fields":{}}'


def test_specialized_provider_is_minimal_structural_protocol() -> None:
    assert IntentPreparationProvider._is_protocol
    assert tuple(inspect.signature(IntentPreparationProvider.prepare).parameters) == (
        "self",
        "text",
    )
    assert get_type_hints(IntentPreparationProvider.prepare) == {
        "text": str,
        "return": str,
    }
    assert not hasattr(IntentPreparationProvider, "generate")
    provider: IntentPreparationProvider = FakePreparationProvider()
    assert provider.prepare("Texto limitado") == (
        '{"outcome":"unsupported","intent":null,"fields":{}}'
    )
    assert not hasattr(provider, "execute")


def test_core_package_imports_only_standard_library_and_its_own_capability() -> None:
    package = Path(__file__).resolve().parents[4] / "app/cognition/intent_preparation"
    sources = sorted(package.glob("*.py"))
    assert len(sources) == 7
    for source in sources:
        tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                assert module.split(".", 1)[
                    0
                ] in sys.stdlib_module_names or module.startswith(
                    "app.cognition.intent_preparation."
                ), (source.name, module)
                assert module.split(".", 1)[0] not in {
                    "http",
                    "urllib",
                    "socket",
                    "subprocess",
                    "importlib",
                }, (source.name, module)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}
