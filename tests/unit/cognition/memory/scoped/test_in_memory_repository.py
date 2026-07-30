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


def test_constructor_copies_mutable_input_and_rejects_unscoped_values() -> None:
    scope = MemoryScope("scope-a")
    owned = record(scope, "content")
    initial = [owned]
    repository = InMemoryScopedMemoryRepository(initial)
    initial.clear()

    assert repository.search(scope, "content") == (owned,)
    with pytest.raises(TypeError):
        InMemoryScopedMemoryRepository((object(),))  # type: ignore[arg-type]


def test_add_preserves_order_duplicates_and_scope_isolation() -> None:
    scope_a = MemoryScope("scope-a")
    scope_b = MemoryScope("scope-b")
    first = record(scope_a, "Shared prompt first")
    second = record(scope_a, "Shared prompt second")
    other = record(scope_b, "Shared prompt other")
    repository = InMemoryScopedMemoryRepository()

    repository.add(first)
    repository.add(first)
    repository.add(second)
    repository.add(other)

    assert repository.search(scope_a, "Shared prompt") == (
        first,
        first,
        second,
    )
    assert repository.search(scope_b, "Shared prompt") == (other,)


def test_add_requires_and_preserves_exact_validated_record() -> None:
    scope = MemoryScope("scope-a")
    owned = record(scope, "Stable content")
    repository = InMemoryScopedMemoryRepository()

    repository.add(owned)

    assert repository.search(scope, "Stable") == (owned,)
    assert repository.search(scope, "Stable")[0] is owned
    with pytest.raises(TypeError):
        repository.add(object())  # type: ignore[arg-type]


def test_repository_has_only_explicit_read_and_append_surface() -> None:
    repository = InMemoryScopedMemoryRepository()
    public_names = {
        name for name in dir(repository) if not name.startswith("_")
    }

    assert public_names == {"add", "search"}
    assert "scope" in signature(repository.search).parameters
    assert "record" in signature(repository.add).parameters
    assert not public_names & {
        "clear",
        "delete",
        "flush",
        "global_search",
        "recall_all",
        "save_all",
        "search_all",
        "update",
        "upsert",
    }
