"""Tests for repository-backed contextual memory retrieval."""

from unittest.mock import Mock

import pytest

from app.cognition.memory.scoped.context_retriever import (
    RepositoryMemoryContextRetriever,
)
from app.cognition.memory.scoped.contracts import ScopedMemoryRepository
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)


def test_construction_does_not_search() -> None:
    repository = Mock(spec=ScopedMemoryRepository)

    RepositoryMemoryContextRetriever(repository)

    repository.search.assert_not_called()


def test_retrieve_searches_once_and_builds_scoped_snapshot() -> None:
    scope = MemoryScope("scope-a")
    records = (ScopedMemoryRecord(scope, "matching content"),)
    repository = Mock(spec=ScopedMemoryRepository)
    repository.search.return_value = records

    snapshot = RepositoryMemoryContextRetriever(repository).retrieve(
        scope, "matching"
    )

    assert snapshot == MemorySnapshot(scope, records)
    repository.search.assert_called_once_with(scope, "matching")


def test_empty_result_preserves_requested_scope() -> None:
    scope = MemoryScope("scope-a")
    repository = Mock(spec=ScopedMemoryRepository)
    repository.search.return_value = ()

    snapshot = RepositoryMemoryContextRetriever(repository).retrieve(
        scope, "missing"
    )

    assert snapshot == MemorySnapshot(scope, ())


def test_repository_error_propagates_without_retry_or_fallback() -> None:
    repository = Mock(spec=ScopedMemoryRepository)
    repository.search.side_effect = RuntimeError("controlled failure")
    retriever = RepositoryMemoryContextRetriever(repository)

    with pytest.raises(RuntimeError, match="controlled failure"):
        retriever.retrieve(MemoryScope("scope-a"), "query")

    repository.search.assert_called_once()
