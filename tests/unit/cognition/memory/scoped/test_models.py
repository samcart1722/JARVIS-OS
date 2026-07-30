"""Tests for immutable scope-owned memory models."""

from dataclasses import FrozenInstanceError
from inspect import signature

import pytest

from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)


def test_scope_accepts_an_explicit_opaque_identifier() -> None:
    assert MemoryScope("session-17").identifier == "session-17"


@pytest.mark.parametrize("identifier", ("", " ", "\t\n"))
def test_scope_rejects_empty_or_whitespace_identifier(identifier: str) -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        MemoryScope(identifier)


def test_scope_is_immutable_comparable_and_hashable() -> None:
    first = MemoryScope("scope-a")
    second = MemoryScope("scope-a")

    assert first == second
    assert {first: "owned"}[second] == "owned"
    with pytest.raises(FrozenInstanceError):
        first.identifier = "scope-b"  # type: ignore[misc]


def test_scope_has_no_default_or_automatic_generation() -> None:
    parameter = signature(MemoryScope).parameters["identifier"]

    assert parameter.default is parameter.empty
    with pytest.raises(TypeError):
        MemoryScope()  # type: ignore[call-arg]


def test_record_requires_scope_and_preserves_normalized_content() -> None:
    record = ScopedMemoryRecord(
        scope=MemoryScope("scope-a"),
        content="  Stable content  ",
    )

    assert record.content == "Stable content"
    with pytest.raises(TypeError):
        ScopedMemoryRecord(scope=None, content="content")  # type: ignore[arg-type]


def test_record_is_immutable() -> None:
    record = ScopedMemoryRecord(MemoryScope("scope-a"), "content")

    with pytest.raises(FrozenInstanceError):
        record.content = "changed"  # type: ignore[misc]


def test_empty_snapshot_is_valid_for_explicit_scope() -> None:
    scope = MemoryScope("scope-a")

    assert MemorySnapshot(scope=scope).records == ()


def test_snapshot_preserves_order_and_requires_matching_scope() -> None:
    scope = MemoryScope("scope-a")
    records = (
        ScopedMemoryRecord(scope, "first"),
        ScopedMemoryRecord(scope, "second"),
    )

    assert MemorySnapshot(scope, records).records == records
    with pytest.raises(ValueError):
        MemorySnapshot(
            scope,
            (ScopedMemoryRecord(MemoryScope("scope-b"), "other"),),
        )


def test_snapshot_and_record_collection_are_immutable() -> None:
    snapshot = MemorySnapshot(MemoryScope("scope-a"))

    with pytest.raises(FrozenInstanceError):
        snapshot.scope = MemoryScope("scope-b")  # type: ignore[misc]
    with pytest.raises(TypeError):
        MemorySnapshot(snapshot.scope, [])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        MemorySnapshot(None)  # type: ignore[arg-type]
