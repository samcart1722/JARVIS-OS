# Sprint 22 Summary

Sprint 22 implements the first durable local knowledge and state foundation in
the feature working tree. An explicitly opened SQLite schema v1 persists
workspace-scoped structured lists and one minimal immutable typed knowledge
record with exact provenance. The Core continues to depend on repository
Protocols rather than `sqlite3`.

List behavior remains compatible with Sprint 21: surrounding whitespace is
trimmed, duplicates compare by case-folding, first accepted display form and
insertion order survive, and immutable snapshots report added versus existing
items. Knowledge identity is `workspace_id + record_id`; identical storage is
idempotent, different content conflicts safely, and absent reads return
`local_knowledge_not_found`.

Authorization precedes every repository read and write. Success, denial,
validation failure, conflict, not-found, and `not_handled` are terminal local
results with no model or external access. Tests observe Ollama, readiness, and
HTTP request boundaries. The public HTTP API and historical reasoning path are
unchanged.

The controlled CLI runs `seed` and `verify` in separate processes against a
caller-supplied database outside the repository. Default `Container`
construction remains inert and in-memory.

Limitations remain: no authenticated identity, natural-language routing,
public local-first API, automatic local-to-reasoning bridge, sync, encryption,
delete/retention policy, semantic retrieval, truth validation, automatic
ingestion, or prompt integration. This is not a complete Knowledge Engine.

Sprint 22 is implemented but not committed, merged, or tagged. The base remains
`8c0330b54fca07eb2fe03657f499bc7fbac9e898` with tag
`sprint-21-complete`. Validation after focused review corrections reports 570
configured tests passed, Ruff clean, and `git diff --check` clean. The prior
Sprint 22 implementation result was 561 passed. Constitution and ADR statuses
are unchanged.
