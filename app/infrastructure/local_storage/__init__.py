"""Explicit local durable-storage adapters."""

from app.infrastructure.local_storage.sqlite_storage import (
    SCHEMA_VERSION,
    SQLiteLocalStorage,
    SQLitePermissionGrantRepository,
    SQLitePrincipalActorMappingRepository,
    UnsupportedSchemaVersion,
)

__all__ = [
    "SCHEMA_VERSION",
    "SQLiteLocalStorage",
    "SQLitePermissionGrantRepository",
    "SQLitePrincipalActorMappingRepository",
    "UnsupportedSchemaVersion",
]
