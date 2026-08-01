"""SQLite schema and durable repository behavior."""

import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.cognition.local_resolution.contracts import KnowledgeRecordConflict
from app.cognition.local_resolution.models import (
    KnowledgeKind,
    KnowledgeProvenance,
    KnowledgeRecord,
    WorkspaceIdentity,
)
from app.infrastructure.local_storage.sqlite_storage import (
    SCHEMA_VERSION,
    SQLiteKnowledgeRecordRepository,
    SQLiteLocalStorage,
    UnsupportedSchemaVersion,
)


def _record(workspace: WorkspaceIdentity, value: str = "4") -> KnowledgeRecord:
    return KnowledgeRecord(
        "family.child.diaper-size",
        workspace,
        KnowledgeKind.FACT,
        "child.diaper_size",
        value,
        KnowledgeProvenance("user_asserted", "actor:wife"),
    )


def test_constructor_is_inert_and_initialization_is_explicit(tmp_path) -> None:
    path = tmp_path / "nested" / "local.sqlite3"
    storage = SQLiteLocalStorage(path)
    assert not path.exists() and not storage.is_open
    with pytest.raises(sqlite3.OperationalError):
        storage.open()
    assert not path.exists()


@pytest.mark.parametrize("invalid_path", ("", "   ", Path("."), "directory/"))
def test_constructor_rejects_paths_without_usable_filename(
    invalid_path, tmp_path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = tuple(tmp_path.iterdir())
    with pytest.raises(ValueError, match="filename"):
        SQLiteLocalStorage(invalid_path)
    assert tuple(tmp_path.iterdir()) == before


def test_valid_relative_filename_is_accepted_and_inert(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    storage = SQLiteLocalStorage("local.sqlite3")
    assert storage.database_path == Path("local.sqlite3")
    assert not storage.is_open
    assert tuple(tmp_path.iterdir()) == ()


def test_new_database_schema_version_and_idempotent_reopen(tmp_path) -> None:
    path = tmp_path / "local.sqlite3"
    first = SQLiteLocalStorage(path)
    try:
        first.open()
        first.initialize()
        assert first.is_open
    finally:
        first.close()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert connection.execute(
            "SELECT schema_version FROM schema_metadata WHERE schema_key = ?",
            ("local_storage",),
        ).fetchone() == (SCHEMA_VERSION,)
    second = SQLiteLocalStorage(path)
    try:
        second.open()
        second.initialize()
    finally:
        second.close()


def test_newer_schema_is_rejected_before_modification(tmp_path) -> None:
    path = tmp_path / "future.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
        connection.execute("CREATE TABLE future_marker (value TEXT)")
    storage = SQLiteLocalStorage(path)
    try:
        storage.open()
        with pytest.raises(UnsupportedSchemaVersion):
            storage.initialize()
    finally:
        storage.close()
    with sqlite3.connect(path) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
            )
        }
    assert names == {"future_marker"}


def test_lists_persist_order_duplicates_isolation_and_snapshot(tmp_path) -> None:
    path = tmp_path / "lists.sqlite3"
    one, two = WorkspaceIdentity("one"), WorkspaceIdentity("two")
    first = SQLiteLocalStorage(path)
    try:
        first.open()
        first.initialize()
        added = first.add(one, "shopping", ("diapers", "Gerber", "grapes"))
        duplicate = first.add(one, "shopping", ("GRAPES", "milk"))
        snapshot = first.read(one, "shopping")
        first.add(one, "shopping", ("later",))
        first.add(one, "other'; DROP TABLE list_items; --", ("safe",))
        assert added.added == ("diapers", "Gerber", "grapes")
        assert duplicate.already_present == ("GRAPES",)
        assert snapshot.items == ("diapers", "Gerber", "grapes", "milk")
    finally:
        first.close()
    second = SQLiteLocalStorage(path)
    try:
        second.open()
        second.initialize()
        assert second.read(one, "shopping").items == (
            "diapers", "Gerber", "grapes", "milk", "later"
        )
        assert second.read(two, "shopping").items == ()
        assert second.read(one, "other'; DROP TABLE list_items; --").items == ("safe",)
    finally:
        second.close()


def test_knowledge_round_trip_idempotency_conflict_and_workspace_identity(
    tmp_path,
) -> None:
    path = tmp_path / "knowledge.sqlite3"
    one, two = WorkspaceIdentity("one"), WorkspaceIdentity("two")
    first = SQLiteLocalStorage(path)
    try:
        first.open()
        first.initialize()
        repository = SQLiteKnowledgeRecordRepository(first)
        record = _record(one)
        assert repository.store(record).created
        assert not repository.store(record).created
        with pytest.raises(KnowledgeRecordConflict):
            repository.store(_record(one, "5"))
        other_record = KnowledgeRecord(
            record.record_id,
            two,
            record.kind,
            record.key,
            "independent",
            record.provenance,
        )
        assert repository.store(other_record).created
    finally:
        first.close()
    second = SQLiteLocalStorage(path)
    try:
        second.open()
        second.initialize()
        repository = SQLiteKnowledgeRecordRepository(second)
        recovered = repository.read(one, record.record_id).record
        assert recovered == record
        assert recovered.provenance == record.provenance
        assert repository.read(two, record.record_id).record == other_record
        assert (
            repository.read(WorkspaceIdentity("three"), record.record_id).record
            is None
        )
        with pytest.raises(FrozenInstanceError):
            recovered.value = "changed"
    finally:
        second.close()
