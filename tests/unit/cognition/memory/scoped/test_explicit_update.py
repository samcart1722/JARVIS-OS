"""Tests for the explicit scoped memory update service."""

from unittest.mock import Mock, call

import pytest

from app.cognition.memory.scoped.contracts import ScopedMemoryWriter
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
    MemoryUpdateDisabledError,
)
from app.cognition.memory.scoped.models import MemoryScope, ScopedMemoryRecord


def test_construction_and_disabled_update_do_not_write() -> None:
    writer = Mock(spec=ScopedMemoryWriter)
    service = ExplicitMemoryUpdateService(writer, enabled=False)

    assert service.enabled is False
    writer.add.assert_not_called()
    with pytest.raises(MemoryUpdateDisabledError, match="disabled"):
        service.remember(MemoryScope("scope-a"), "content")
    writer.add.assert_not_called()


@pytest.mark.parametrize("content", ("", "  "))
def test_enabled_update_rejects_empty_content(content: str) -> None:
    writer = Mock(spec=ScopedMemoryWriter)
    service = ExplicitMemoryUpdateService(writer, enabled=True)

    with pytest.raises(ValueError, match="cannot be empty"):
        service.remember(MemoryScope("scope-a"), content)

    writer.add.assert_not_called()


def test_enabled_update_requires_explicit_scope() -> None:
    writer = Mock(spec=ScopedMemoryWriter)
    service = ExplicitMemoryUpdateService(writer, enabled=True)

    with pytest.raises(TypeError, match="MemoryScope"):
        service.remember(None, "content")  # type: ignore[arg-type]

    writer.add.assert_not_called()


def test_enabled_update_adds_and_returns_exact_normalized_record() -> None:
    writer = Mock(spec=ScopedMemoryWriter)
    service = ExplicitMemoryUpdateService(writer, enabled=True)
    scope = MemoryScope("scope-a")

    result = service.remember(scope, "  explicit content  ")

    assert result == ScopedMemoryRecord(scope, "explicit content")
    writer.add.assert_called_once_with(result)


def test_duplicates_produce_two_independent_writes() -> None:
    writer = Mock(spec=ScopedMemoryWriter)
    service = ExplicitMemoryUpdateService(writer, enabled=True)
    scope = MemoryScope("scope-a")

    first = service.remember(scope, "same")
    second = service.remember(scope, "same")

    assert first == second
    assert writer.add.call_args_list == [call(first), call(second)]


def test_unexpected_writer_error_propagates() -> None:
    writer = Mock(spec=ScopedMemoryWriter)
    writer.add.side_effect = RuntimeError("write failed")
    service = ExplicitMemoryUpdateService(writer, enabled=True)

    with pytest.raises(RuntimeError, match="write failed"):
        service.remember(MemoryScope("scope-a"), "content")
