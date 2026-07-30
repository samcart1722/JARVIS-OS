# Sprint 12 Summary — Scoped Memory Persistence Foundation v1

## Reason for the foundation

The initial engine integration was stopped because the global repository
returns all active memories, existing entities carry no ownership, and the
legacy adapter uses that path. Connecting it risked cross-scope disclosure.

## Implemented boundary

The parallel `app/cognition/memory/scoped` package provides immutable
`MemoryScope`, immutable owned `ScopedMemoryRecord`, the read-only
`ScopedMemoryRepository.search(scope, query)` contract, and an in-memory
implementation initialized from an immutable tuple.

Construction groups records by scope. Search directly selects only the
requested scope's bucket before applying a case-insensitive literal substring
match. Constructor order is preserved. Blank values are rejected. There is no
`search_all` or write surface.

`MemoryFact` was not composed into the record because its operational fields,
tags, metadata, confidence, version, and active state are mutable. The new
record uses only its stable existing content concept.

## Isolation and legacy

Tests prove identical content remains isolated between scopes A and B and that
a query matching only B returns nothing for A. The implementation neither
imports nor wraps the global repository or `LegacyMemoryAdapter`.

Legacy data without ownership is not migrated, assigned an invented scope, or
exposed. A future explicit migration policy is required.

## Deliberate non-integration

No change was made to CognitiveEngine, CognitiveContext, Container, Settings,
capabilities, reasoning, Ollama, readiness, demo, CLI, API, or legacy memory.
There is no external I/O, persistence, embedding, ranking, semantic search,
Memory Update, or active write API.

Sprint 13 is the next controlled read-only integration point. Migration,
writes, durable persistence, and safe prompt use remain roadmap items.
