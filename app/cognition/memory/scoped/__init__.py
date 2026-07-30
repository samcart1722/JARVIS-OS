"""Scope-isolated memory persistence foundation."""

from app.cognition.memory.scoped.context_retriever import (
    RepositoryMemoryContextRetriever,
)
from app.cognition.memory.scoped.contracts import (
    MemoryContextRetriever,
    ScopedMemoryRepository,
    ScopedMemoryWriter,
)
from app.cognition.memory.scoped.explicit_update import (
    ExplicitMemoryUpdateService,
    MemoryUpdateDisabledError,
)
from app.cognition.memory.scoped.in_memory_repository import (
    InMemoryScopedMemoryRepository,
)
from app.cognition.memory.scoped.models import (
    MemoryScope,
    MemorySnapshot,
    ScopedMemoryRecord,
)

__all__ = (
    "InMemoryScopedMemoryRepository",
    "ExplicitMemoryUpdateService",
    "MemoryContextRetriever",
    "MemoryUpdateDisabledError",
    "MemoryScope",
    "MemorySnapshot",
    "RepositoryMemoryContextRetriever",
    "ScopedMemoryRecord",
    "ScopedMemoryRepository",
    "ScopedMemoryWriter",
)
