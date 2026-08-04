# Sprint 25 Summary — Deterministic Local Knowledge Commands v1

Sprint 24 is completed at merge
`fe958f45409c0fc11df38cd945ae9678e3ad9e23`, tag `sprint-24-complete`.
Sprint 25 remains uncommitted, unmerged, and untagged in its feature working
tree.

The existing interpreter now accepts strict JSON `knowledge read` and
`knowledge store` commands and creates the existing typed knowledge intents.
Duplicate JSON keys and malformed, trailing, non-object, incomplete, unknown,
non-string, blank, or invalid-kind payloads produce stable terminal reasons.
This is not general natural-language understanding.

Workspace comes only from `TextRoutingRequest`; caller-supplied provenance is
preserved. The existing router, coordinator, resolver, knowledge capability,
permission ordering, repositories and immutable conflict, idempotency and
not-found semantics remain intact. Public HTTP, `CognitiveEngine`, Settings,
schema, providers and external access are unchanged.

Implementation validation passed **680 tests** with `DEBUG=true`. Ruff and
`git diff --check` were clean using a controlled external pytest temporary
directory.

The operational demo observes actual composed boundaries: one cognitive
processor invocation in the authorized unrelated scenario and zero provider,
Ollama-client, readiness and network invocations.

New technical debt: none identified. Broader grammar, multilingual and
conversational context, fuzzy or model-assisted extraction, public exposure,
authentication/RBAC, semantic retrieval, synchronization, encryption,
retention and external access remain deliberate deferrals. Constitution and
ADR standards remain Draft; no approved ADR is asserted.
