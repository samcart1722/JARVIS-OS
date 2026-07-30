"""Tests for the scope-isolated in-memory repository."""

from inspect import signature

import pytest

from app.cognition.memory.scoped.in_memory_repository import (
    InMemoryScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import (
    MemoryScope,
    ScopedMemoryRecord,
)


def record(scope: MemoryScope, content: str) -> ScopedMemoryRecord:
    return ScopedMemoryRecord(scope=scope, content=content)


def test_empty_construction_and_unowned_scope_return_empty_tuple() -> None:
    repository = InMemoryScopedMemoryRepository()

    result = repository.search(MemoryScope("unowned"), "query")

    assert result == ()
    assert isinstance(result, tuple)


def test_search_requires_scope_and_non_empty_query() -> None:
    repository = InMemoryScopedMemoryRepository()

    with pytest.raises(TypeError):
        repository.search(None, "query")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        repository.search(MemoryScope("scope-a"), " ")


def test_scope_a_and_b_are_isolated_even_for_identical_text() -> None:
    scope_a = MemoryScope("scope-a")
    scope_b = MemoryScope("scope-b")
    owned_a = record(scope_a, "Shared matching content")
    owned_b = record(scope_b, "Shared matching content")
    repository = InMemoryScopedMemoryRepository((owned_a, owned_b))

    assert repository.search(scope_a, "matching") == (owned_a,)
    assert repository.search(scope_b, "matching") == (owned_b,)


def test_query_never_expands_search_to_another_scope() -> None:
    scope_a = MemoryScope("scope-a")
    scope_b = MemoryScope("scope-b")
    secret_b = record(scope_b, "Unique phrase visible only in B")
    repository = InMemoryScopedMemoryRepository(
        (record(scope_a, "Different content"), secret_b)
    )

    assert repository.search(scope_a, "Unique phrase") == ()


def test_literal_case_insensitive_search_preserves_constructor_order() -> None:
    scope = MemoryScope("scope-a")
    first = record(scope, "Architecture note one")
    second = record(scope, "ARCHITECTURE note two")
    repository = InMemoryScopedMemoryRepository((first, second))

    expected = (first, second)
    assert repository.search(scope, "architecture") == expected
    assert repository.search(scope, "ARCHITECTURE") == expected
    assert repository.search(scope, "architecture") == expected


def test_results_and_constructor_input_are_not_mutated_or_shared() -> None:
    scope = MemoryScope("scope-a")
    owned = record(scope, "Stable content")
    initial = (owned,)
    repository = InMemoryScopedMemoryRepository(initial)

    result = repository.search(scope, "stable")

    assert result == initial
    assert result is not initial
    assert initial == (owned,)
    with pytest.raises(AttributeError):
        result.append(owned)  # type: ignore[attr-defined]


def test_constructor_rejects_mutable_or_unscoped_input() -> None:
    scope = MemoryScope("scope-a")

    with pytest.raises(TypeError):
        InMemoryScopedMemoryRepository([record(scope, "content")])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        InMemoryScopedMemoryRepository((object(),))  # type: ignore[arg-type]


def test_repository_has_no_global_search_or_write_surface() -> None:
    repository = InMemoryScopedMemoryRepository()
    public_names = {
        name for name in dir(repository) if not name.startswith("_")
    }

    assert public_names == {"search"}
    assert "scope" in signature(repository.search).parameters
